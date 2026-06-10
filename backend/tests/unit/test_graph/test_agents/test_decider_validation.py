# tests/unit/test_graph/test_agents/test_decider_validation.py
"""Decider 거래 실행 가능성 검증(validation.py) 단위 테스트"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from data.schemas import PortfolioOut, PositionOut
from graph.agents.decider.validation import build_validated_decisions


def make_position(ticker: str, shares: str, avg_price: str, position_id: int = 1) -> PositionOut:
    return PositionOut(
        id=position_id,
        portfolio_id=1,
        ticker=ticker,
        total_shares=Decimal(shares),
        avg_buy_price=Decimal(avg_price),
        updated_at=datetime.now(timezone.utc),
    )


def make_decision(ticker: str, action: str, target_weight_pct: float = 0.0, reason: str = "test") -> dict:
    return {
        "ticker": ticker,
        "action": action,
        "target_weight_pct": target_weight_pct,
        "reason": reason,
        "risk_notes": [],
    }


@pytest.mark.unit
class TestBuildValidatedDecisions:
    """검증 시나리오: 현금 1,000 + AAPL 10주@150 + TSLA 5주@100 = 총 가치 3,000"""

    @pytest.fixture
    def portfolio(self) -> PortfolioOut:
        return PortfolioOut(
            id=1,
            user_id=1,
            base_currency="USD",
            cash=Decimal("1000"),
            updated_at=datetime.now(timezone.utc),
            positions=[
                make_position("AAPL", "10", "100", position_id=1),
                make_position("TSLA", "5", "200", position_id=2),
            ],
        )

    @pytest.fixture
    def prices(self) -> dict:
        return {"AAPL": 150.0, "TSLA": 100.0, "NVDA": 500.0}

    def test_sell_exits_full_position(self, portfolio, prices):
        decisions, final_pf = build_validated_decisions(
            [make_decision("TSLA", "SELL")], portfolio, prices, {}, {}
        )
        assert decisions[0].shares_to_trade == -5.0
        assert decisions[0].trade_value == -500.0
        assert all(p.ticker != "TSLA" for p in final_pf.positions)

    def test_trim_cannot_exceed_held_shares(self, portfolio, prices):
        # TSLA 현재 비중 16.67% → 5%로 축소해도 매도 수량은 보유분 이내
        decisions, _ = build_validated_decisions(
            [make_decision("TSLA", "TRIM", target_weight_pct=5.0)], portfolio, prices, {}, {}
        )
        assert -5.0 <= decisions[0].shares_to_trade < 0

    def test_trim_above_current_weight_is_noop(self, portfolio, prices):
        decisions, _ = build_validated_decisions(
            [make_decision("TSLA", "TRIM", target_weight_pct=50.0)], portfolio, prices, {}, {}
        )
        assert decisions[0].shares_to_trade == 0.0
        assert any("거래 없음" in note for note in decisions[0].risk_notes)

    def test_buys_scaled_down_to_cash_budget(self, portfolio, prices):
        # 매수 요청: AAPL 50%→60% (300) + NVDA 0%→50% (1500) = 1800
        # 가용 한도: 현금 1000 + TSLA 매도 500 - 현금바닥 150 = 1350 → 75%로 축소
        decisions, final_pf = build_validated_decisions(
            [
                make_decision("AAPL", "BUY", target_weight_pct=60.0),
                make_decision("TSLA", "SELL"),
                make_decision("NVDA", "BUY", target_weight_pct=50.0),
            ],
            portfolio,
            prices,
            {},
            {},
        )
        buy_total = sum(d.trade_value for d in decisions if d.trade_value > 0)
        assert buy_total == pytest.approx(1350.0)
        assert any("축소" in note for d in decisions if d.action == "BUY" for note in d.risk_notes)
        # 현금 바닥(총 가치의 5% = 150) 유지
        assert float(final_pf.cash) == pytest.approx(150.0)

    def test_buy_canceled_when_no_budget(self, prices):
        # 현금(10)이 현금 바닥(총 가치 1510의 5% = 75.5) 이하면 매수는 HOLD로 전환
        portfolio = PortfolioOut(
            id=1,
            user_id=1,
            base_currency="USD",
            cash=Decimal("10"),
            updated_at=datetime.now(timezone.utc),
            positions=[make_position("AAPL", "10", "100")],
        )
        decisions, _ = build_validated_decisions(
            [make_decision("NVDA", "BUY", target_weight_pct=10.0)], portfolio, prices, {}, {}
        )
        assert decisions[0].action == "HOLD"
        assert decisions[0].shares_to_trade == 0.0
        assert any("매수 취소" in note for note in decisions[0].risk_notes)

    def test_buy_with_target_below_current_becomes_hold(self, portfolio, prices):
        # AAPL 현재 비중 50% → 목표 30% BUY는 모순 → 거래 없음 + HOLD 표기
        decisions, _ = build_validated_decisions(
            [make_decision("AAPL", "BUY", target_weight_pct=30.0)], portfolio, prices, {}, {}
        )
        assert decisions[0].action == "HOLD"
        assert decisions[0].shares_to_trade == 0.0

    def test_non_buy_decision_for_unheld_ticker_is_dropped(self, portfolio, prices):
        decisions, _ = build_validated_decisions(
            [make_decision("MSFT", "SELL"), make_decision("MSFT", "HOLD")], portfolio, prices, {}, {}
        )
        assert decisions == []

    def test_buy_without_price_is_dropped(self, portfolio, prices):
        decisions, _ = build_validated_decisions(
            [make_decision("UNKNOWN", "BUY", target_weight_pct=10.0)], portfolio, prices, {}, {}
        )
        assert decisions == []

    def test_unknown_action_becomes_hold(self, portfolio, prices):
        decisions, _ = build_validated_decisions(
            [make_decision("AAPL", "YOLO", target_weight_pct=10.0)], portfolio, prices, {}, {}
        )
        assert decisions[0].action == "HOLD"
        assert decisions[0].shares_to_trade == 0.0

    def test_scores_recomputed_with_clamped_adjustment(self, portfolio, prices):
        # adjustment 0.5는 ±0.15로 클램프 → TOTAL = 0.65×MOMO + 0.35×FUND
        decisions, _ = build_validated_decisions(
            [make_decision("AAPL", "HOLD")],
            portfolio,
            prices,
            momo_by_ticker={"AAPL": 70},
            fund_by_ticker={"AAPL": 60},
            adjustment=0.5,
        )
        assert decisions[0].momo_score == 70.0
        assert decisions[0].fund_score == 60.0
        assert decisions[0].total_score == pytest.approx(0.65 * 70 + 0.35 * 60, abs=0.1)

    def test_missing_scores_noted(self, portfolio, prices):
        decisions, _ = build_validated_decisions(
            [make_decision("AAPL", "HOLD")], portfolio, prices, {}, {}
        )
        notes = decisions[0].risk_notes
        assert any("모멘텀 점수 누락" in n for n in notes)
        assert any("펀더멘털 점수 누락" in n for n in notes)

    def test_new_buy_creates_virtual_position(self, portfolio, prices):
        decisions, final_pf = build_validated_decisions(
            [make_decision("NVDA", "BUY", target_weight_pct=10.0)], portfolio, prices, {}, {}
        )
        nvda = next(p for p in final_pf.positions if p.ticker == "NVDA")
        assert nvda.id == 0  # 아직 DB에 없는 가상 포지션
        assert float(nvda.avg_buy_price) == 500.0
        assert float(nvda.total_shares) == pytest.approx(decisions[0].shares_to_trade)

    def test_final_portfolio_cash_is_consistent(self, portfolio, prices):
        decisions, final_pf = build_validated_decisions(
            [make_decision("AAPL", "BUY", target_weight_pct=55.0), make_decision("TSLA", "TRIM", target_weight_pct=10.0)],
            portfolio,
            prices,
            {},
            {},
        )
        net_trade = sum(d.trade_value for d in decisions)
        assert float(final_pf.cash) == pytest.approx(1000.0 - net_trade, abs=0.01)
