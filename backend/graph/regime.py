# graph/regime.py
"""시장 국면(regime) 신호: SPY 지표 3개로 risk_on / neutral / risk_off 판정.

LLM은 시장 국면을 일관되게 오판하므로(상승장 과보수, 하락장 과공격 — FINSABER),
국면 판정은 명시적 수식으로만 한다. 판정 결과는:
  - DECIDER 매수 임계값 (BUY_THRESHOLDS)
  - 신규 후보 추가 기준 (CANDIDATE_BUY_EXTRA)
  - 현금 바닥 (CASH_FLOOR_PCT — validation이 코드로 강제)
에 반영된다.
"""
import logging
import math
import statistics
from datetime import date
from typing import Any, Dict

logger = logging.getLogger(__name__)

BENCHMARK_TICKER = "SPY"
MA_DAYS = 200  # 장기 추세 기준선
VOL_DAYS = 20  # 실현 변동성 측정 창
TRADING_DAYS_PER_YEAR = 252

# 판정 기준 (Phase 4 백테스트로 튜닝 예정)
RISK_OFF_DRAWDOWN = -0.15  # 고점 대비 이만큼 빠지면 무조건 risk_off
RISK_OFF_DRAWDOWN_BELOW_MA = -0.10  # 추세선 아래에서는 이만큼만 빠져도 risk_off
RISK_OFF_VOL = 0.30  # 연환산 변동성이 이 이상이면 risk_off
RISK_ON_MAX_DRAWDOWN = -0.05  # risk_on 조건: 골짜기가 이보다 얕고
RISK_ON_MAX_VOL = 0.20  # 변동성이 이보다 낮고, 추세선 위

# 국면별 규칙
BUY_THRESHOLDS = {"risk_on": 62, "neutral": 65, "risk_off": 72}
CANDIDATE_BUY_EXTRA = {"risk_on": 0, "neutral": 0, "risk_off": 5}  # 신규 후보는 risk_off에서 +5
CASH_FLOOR_PCT = {"risk_on": 5.0, "neutral": 5.0, "risk_off": 10.0}

NEUTRAL_FALLBACK: Dict[str, Any] = {
    "regime": "neutral",
    "spy_vs_ma200_pct": None,
    "drawdown_pct": None,
    "realized_vol_pct": None,
    "note": "insufficient market data",
}


def classify_regime(closes_by_date: Dict[date, float]) -> Dict[str, Any]:
    """SPY 종가 이력(1년 권장)으로 국면을 판정한다. 데이터 부족 시 neutral."""
    values = [closes_by_date[d] for d in sorted(closes_by_date)]
    if len(values) < MA_DAYS + 1:
        return dict(NEUTRAL_FALLBACK)

    current = values[-1]
    ma200 = sum(values[-MA_DAYS:]) / MA_DAYS
    spy_vs_ma200 = current / ma200 - 1.0
    drawdown = current / max(values) - 1.0

    recent = values[-(VOL_DAYS + 1):]
    daily_returns = [recent[i] / recent[i - 1] - 1.0 for i in range(1, len(recent))]
    realized_vol = statistics.stdev(daily_returns) * math.sqrt(TRADING_DAYS_PER_YEAR)

    if (spy_vs_ma200 < 0 and drawdown < RISK_OFF_DRAWDOWN_BELOW_MA) or drawdown < RISK_OFF_DRAWDOWN or realized_vol > RISK_OFF_VOL:
        regime = "risk_off"
    elif spy_vs_ma200 > 0 and drawdown > RISK_ON_MAX_DRAWDOWN and realized_vol < RISK_ON_MAX_VOL:
        regime = "risk_on"
    else:
        regime = "neutral"

    return {
        "regime": regime,
        "spy_vs_ma200_pct": round(spy_vs_ma200 * 100, 1),
        "drawdown_pct": round(drawdown * 100, 1),
        "realized_vol_pct": round(realized_vol * 100, 1),
    }


def regime_rules(regime: str) -> Dict[str, Any]:
    """국면별 의사결정 규칙. 알 수 없는 국면은 neutral 규칙."""
    if regime not in BUY_THRESHOLDS:
        regime = "neutral"
    buy_threshold = BUY_THRESHOLDS[regime]
    return {
        "buy_threshold": buy_threshold,
        "candidate_buy_threshold": buy_threshold + CANDIDATE_BUY_EXTRA[regime],
        "cash_floor_pct": CASH_FLOOR_PCT[regime],
    }


def get_market_regime() -> Dict[str, Any]:
    """SPY 1년 이력을 조회해 국면을 판정한다. 조회 실패 시 neutral 폴백."""
    from .feedback import fetch_closes  # 지연 임포트 (순환 방지)

    try:
        closes = fetch_closes(BENCHMARK_TICKER, period="1y")
        return classify_regime(closes)
    except Exception as e:
        logger.error(f"Failed to compute market regime; falling back to neutral: {e}")
        return dict(NEUTRAL_FALLBACK)
