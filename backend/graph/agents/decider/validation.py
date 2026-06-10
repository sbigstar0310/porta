# agents/decider/validation.py
"""LLM 매매 결정의 실행 가능성 검증 및 수치 재계산.

신뢰 경계: LLM 출력에서 사용하는 것은 action / target_weight_pct / reason / risk_notes 뿐이다.
수량·금액·점수·현재비중·최종 포트폴리오는 실제 포트폴리오와 시세로 코드가 계산한다.

처리 흐름 (build_validated_decisions):
    1. _build_intent       : LLM 결정 1건 → 거래 의도(TradeIntent). 불가능한 결정은 폐기/보정
    2. _cap_buys_to_budget : 매수 총액을 가용 현금 한도(현금 바닥 유지) 안으로 비례 축소
    3. _to_decision        : 의도 → Decision (점수는 ground-truth로 재계산)
    4. _apply_intents      : 거래를 가상 적용한 최종 포트폴리오 계산 (DB 변경 없음)
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from data.schemas import PortfolioOut, PositionOut
from .schema import Decision

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"BUY", "SELL", "HOLD", "TRIM"}
MIN_SHARES = 1e-9  # 부동소수점 오차로 남는 잔여 수량 제거용
MAX_ADJUSTMENT = 0.05  # 리뷰어 가중치 조정(δ) 허용 범위


@dataclass
class TradeIntent:
    """검증을 통과한 단일 종목의 거래 의도. 수치는 모두 코드가 계산한 값이다."""

    ticker: str
    action: str
    reason: str
    notes: List[str]
    held_shares: float
    price: float
    current_weight_pct: float
    delta_shares: float  # 매수(+) / 매도(-) 수량

    @property
    def trade_value(self) -> float:
        return self.delta_shares * self.price

    @property
    def is_buy(self) -> bool:
        return self.delta_shares > 0


def build_validated_decisions(
    llm_decisions: List[Dict[str, Any]],
    portfolio: PortfolioOut,
    prices: Dict[str, float],
    momo_by_ticker: Dict[str, float],
    fund_by_ticker: Dict[str, float],
    adjustment: float = 0.0,
    cash_floor_pct: float = 5.0,
) -> Tuple[List[Decision], PortfolioOut]:
    """LLM 결정을 실제 포트폴리오 기준으로 검증·클램프하고 최종 포트폴리오를 재계산한다."""
    total_value = _portfolio_total_value(portfolio, prices)
    if total_value <= 0:
        logger.error("Portfolio total value is non-positive; skipping decision validation")
        return [], portfolio

    # 1. 거래 의도 생성 (티커당 1건, 중복은 마지막 결정 사용)
    intents: Dict[str, TradeIntent] = {}
    for raw in llm_decisions:
        intent = _build_intent(raw, portfolio, prices, total_value)
        if intent:
            intents[intent.ticker] = intent

    # 2. 현금 제약 적용
    _cap_buys_to_budget(list(intents.values()), float(portfolio.cash), total_value, cash_floor_pct)

    # 3. Decision 변환 + 4. 최종 포트폴리오 계산
    delta = _clamp(adjustment, -MAX_ADJUSTMENT, MAX_ADJUSTMENT)
    decisions = [_to_decision(i, momo_by_ticker, fund_by_ticker, delta, total_value) for i in intents.values()]
    final_portfolio = _apply_intents(portfolio, intents, prices)
    return decisions, final_portfolio


# ---- 1단계: LLM 결정 → 거래 의도 ----


def _build_intent(
    raw: Dict[str, Any],
    portfolio: PortfolioOut,
    prices: Dict[str, float],
    total_value: float,
) -> Optional[TradeIntent]:
    """LLM 결정 1건을 검증해 거래 의도로 변환한다. 의미 없는 결정은 None으로 폐기."""
    ticker = str(raw.get("ticker", "")).upper().strip()
    if not ticker:
        return None

    action = str(raw.get("action", "HOLD")).upper().strip()
    notes = [str(n) for n in raw.get("risk_notes", [])]
    if action not in VALID_ACTIONS:
        notes.append(f"알 수 없는 액션 '{action}' → HOLD로 처리")
        action = "HOLD"

    position = next((p for p in portfolio.positions if p.ticker == ticker), None)
    held = float(position.total_shares) if position else 0.0
    price = _resolve_price(ticker, prices, position)

    # 미보유 종목(신규 후보)은 BUY만 의미가 있음
    if held <= MIN_SHARES and action != "BUY":
        logger.info(f"Dropping {action} decision for unheld ticker {ticker}")
        return None

    # 시세가 없으면 거래 불가
    if price is None:
        if held <= MIN_SHARES:
            logger.warning(f"Dropping BUY decision for {ticker}: price unavailable")
            return None
        notes.append("시세 조회 실패로 거래 보류 → HOLD")
        action, price = "HOLD", 0.0

    current_weight = held * price / total_value * 100.0
    target_weight = float(raw.get("target_weight_pct") or current_weight)
    delta_shares = _delta_shares(action, target_weight, current_weight, held, price, total_value, notes)

    # 거래가 발생하지 않는 BUY/TRIM은 HOLD로 표기 (보고서 혼란 방지)
    if action in ("BUY", "TRIM") and delta_shares == 0.0:
        action = "HOLD"

    return TradeIntent(
        ticker=ticker,
        action=action,
        reason=str(raw.get("reason", "")),
        notes=notes,
        held_shares=held,
        price=price,
        current_weight_pct=current_weight,
        delta_shares=delta_shares,
    )


def _delta_shares(
    action: str,
    target_weight: float,
    current_weight: float,
    held: float,
    price: float,
    total_value: float,
    notes: List[str],
) -> float:
    """액션과 목표 비중을 실제 거래 수량으로 변환한다. 매도는 보유 수량까지만 허용."""
    if action == "HOLD" or price <= 0:
        return 0.0
    if action == "SELL":
        return -held

    shares = (target_weight - current_weight) / 100.0 * total_value / price
    if action == "TRIM":
        if shares >= 0:
            notes.append("TRIM 목표 비중이 현재 비중 이상 → 거래 없음")
            return 0.0
        return max(shares, -held)

    # BUY
    if shares <= 0:
        notes.append("BUY 목표 비중이 현재 비중 이하 → 거래 없음")
        return 0.0
    return shares


# ---- 2단계: 현금 제약 ----


def _cap_buys_to_budget(
    intents: List[TradeIntent],
    cash: float,
    total_value: float,
    cash_floor_pct: float,
) -> None:
    """매도 대금을 반영한 가용 현금 안으로 매수 총액을 비례 축소한다 (현금 바닥 유지)."""
    sell_proceeds = -sum(i.trade_value for i in intents if i.trade_value < 0)
    buy_total = sum(i.trade_value for i in intents if i.is_buy)
    budget = max(0.0, cash + sell_proceeds - cash_floor_pct / 100.0 * total_value)
    if buy_total <= budget:
        return

    scale = budget / buy_total
    for intent in [i for i in intents if i.is_buy]:
        if scale <= 0:
            intent.notes.append("가용 현금 부족(현금 바닥 유지)으로 매수 취소 → HOLD")
            intent.action = "HOLD"
            intent.delta_shares = 0.0
        else:
            intent.notes.append(f"가용 현금 한도에 맞춰 매수 수량 {scale * 100:.0f}%로 축소")
            intent.delta_shares *= scale


# ---- 3단계: 거래 의도 → Decision ----


def _to_decision(
    intent: TradeIntent,
    momo_by_ticker: Dict[str, float],
    fund_by_ticker: Dict[str, float],
    delta: float,
    total_value: float,
) -> Decision:
    """점수를 ground-truth로 재계산해 Decision을 만든다."""
    momo = momo_by_ticker.get(intent.ticker)
    fund = fund_by_ticker.get(intent.ticker)
    if momo is None:
        intent.notes.append("모멘텀 점수 누락")
    if fund is None:
        intent.notes.append("펀더멘털 점수 누락")
    momo, fund = float(momo or 0.0), float(fund or 0.0)

    final_shares = intent.held_shares + intent.delta_shares
    final_weight = final_shares * intent.price / total_value * 100.0

    return Decision(
        ticker=intent.ticker,
        action=intent.action,
        target_weight_pct=round(final_weight, 2),
        current_weight_pct=round(intent.current_weight_pct, 2),
        shares_to_trade=round(intent.delta_shares, 4),
        trade_value=round(intent.trade_value, 2),
        total_score=round((0.5 + delta) * momo + (0.5 - delta) * fund, 1),
        momo_score=round(momo, 1),
        fund_score=round(fund, 1),
        reason=intent.reason,
        risk_notes=intent.notes,
    )


# ---- 4단계: 최종 포트폴리오 계산 ----


def _apply_intents(
    portfolio: PortfolioOut,
    intents: Dict[str, TradeIntent],
    prices: Dict[str, float],
) -> PortfolioOut:
    """검증된 거래를 가상으로 적용한 최종 포트폴리오를 만든다 (DB는 변경하지 않음)."""
    now = datetime.now(timezone.utc)
    cash = float(portfolio.cash) - sum(i.trade_value for i in intents.values())

    # 기존 포지션 갱신 (전량 매도는 목록에서 제외)
    positions: List[PositionOut] = []
    for pos in portfolio.positions:
        intent = intents.get(pos.ticker)
        new_shares = float(pos.total_shares) + (intent.delta_shares if intent else 0.0)
        if new_shares > MIN_SHARES:
            price = _resolve_price(pos.ticker, prices, pos) or 0.0
            positions.append(_updated_position(pos, new_shares, price, now))

    # 신규 매수 포지션 추가
    held_tickers = {p.ticker for p in portfolio.positions}
    for intent in intents.values():
        if intent.ticker not in held_tickers and intent.delta_shares > MIN_SHARES:
            positions.append(_new_position(portfolio.id, intent, now))

    return _with_totals(portfolio, cash, positions, now)


def _updated_position(pos: PositionOut, new_shares: float, price: float, now: datetime) -> PositionOut:
    avg_buy = float(pos.avg_buy_price)
    has_price = price > 0
    return pos.model_copy(
        update={
            "total_shares": _decimal(new_shares, 4),
            "updated_at": now,
            "current_price": _decimal(price, 4) if has_price else None,
            "current_market_value": _decimal(new_shares * price, 2) if has_price else None,
            "unrealized_pnl": _decimal((price - avg_buy) * new_shares, 2) if has_price else None,
            "unrealized_pnl_pct": _decimal((price - avg_buy) / avg_buy * 100.0, 2) if has_price and avg_buy > 0 else None,
        }
    )


def _new_position(portfolio_id: int, intent: TradeIntent, now: datetime) -> PositionOut:
    return PositionOut(
        id=0,  # 가상 포지션 (아직 DB에 없음)
        portfolio_id=portfolio_id,
        ticker=intent.ticker,
        total_shares=_decimal(intent.delta_shares, 4),
        avg_buy_price=_decimal(intent.price, 4),
        updated_at=now,
        current_price=_decimal(intent.price, 4),
        current_market_value=_decimal(intent.trade_value, 2),
        unrealized_pnl=Decimal("0"),
        unrealized_pnl_pct=Decimal("0"),
    )


def _with_totals(portfolio: PortfolioOut, cash: float, positions: List[PositionOut], now: datetime) -> PortfolioOut:
    total_stock_value = sum(float(p.current_market_value or 0) for p in positions)
    total_pnl = sum(float(p.unrealized_pnl or 0) for p in positions)
    cost_basis = sum(float(p.avg_buy_price) * float(p.total_shares) for p in positions)
    return portfolio.model_copy(
        update={
            "cash": _decimal(cash, 2),
            "updated_at": now,
            "positions": positions,
            "total_stock_value": _decimal(total_stock_value, 2),
            "total_value": _decimal(cash + total_stock_value, 2),
            "total_unrealized_pnl": _decimal(total_pnl, 2),
            "total_unrealized_pnl_pct": _decimal(total_pnl / cost_basis * 100.0, 2) if cost_basis > 0 else None,
        }
    )


# ---- 공용 헬퍼 ----


def _portfolio_total_value(portfolio: PortfolioOut, prices: Dict[str, float]) -> float:
    """검증 기준이 되는 총 가치: 현금 + Σ 보유수량 × 시세."""
    total = float(portfolio.cash)
    for pos in portfolio.positions:
        price = _resolve_price(pos.ticker, prices, pos)
        if price is not None:
            total += float(pos.total_shares) * price
    return total


def _resolve_price(ticker: str, prices: Dict[str, float], position: Optional[PositionOut]) -> Optional[float]:
    """시세 우선순위: 실시간 조회 > 포지션의 현재가 > 평균 매수가."""
    candidates = [prices.get(ticker)]
    if position is not None:
        candidates += [position.current_price, position.avg_buy_price]
    for price in candidates:
        if price and float(price) > 0:
            return float(price)
    return None


def _clamp(value: Any, low: float, high: float) -> float:
    return max(low, min(high, float(value or 0.0)))


def _decimal(value: float, digits: int) -> Decimal:
    return Decimal(str(round(value, digits)))
