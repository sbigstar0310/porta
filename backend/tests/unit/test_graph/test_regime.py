# tests/unit/test_graph/test_regime.py
"""시장 국면 판정(graph/regime.py) 단위 테스트"""
import pytest
from datetime import date, timedelta

from graph.regime import (
    BUY_THRESHOLDS,
    CASH_FLOOR_PCT,
    MA_DAYS,
    classify_regime,
    regime_rules,
)


def make_closes(daily_values):
    """주말 없이 연속된 날짜로 종가 dict 생성 (판정 로직은 날짜 간격과 무관)"""
    start = date(2025, 1, 1)
    return {start + timedelta(days=i): v for i, v in enumerate(daily_values)}


def flat_series(price=100.0, days=MA_DAYS + 30):
    return [price] * days


@pytest.mark.unit
class TestClassifyRegime:
    def test_calm_uptrend_is_risk_on(self):
        # 완만한 상승: 평균선 위, 골짜기 없음, 저변동성
        values = [100.0 + i * 0.1 for i in range(MA_DAYS + 30)]
        result = classify_regime(make_closes(values))
        assert result["regime"] == "risk_on"
        assert result["spy_vs_ma200_pct"] > 0

    def test_deep_drawdown_is_risk_off(self):
        # 고점 후 -20% 급락
        values = flat_series(100.0, MA_DAYS) + [100.0 - i for i in range(1, 21)]
        result = classify_regime(make_closes(values))
        assert result["regime"] == "risk_off"
        assert result["drawdown_pct"] <= -15

    def test_below_ma_with_moderate_drawdown_is_risk_off(self):
        # 평균선 아래 + 고점 대비 -12% (단독 -15% 기준엔 안 걸리지만 추세 붕괴와 결합)
        values = flat_series(100.0, MA_DAYS) + [88.0] * 30
        result = classify_regime(make_closes(values))
        assert result["spy_vs_ma200_pct"] < 0
        assert -15 < result["drawdown_pct"] < -10
        assert result["regime"] == "risk_off"

    def test_high_volatility_alone_is_risk_off(self):
        # 가격 수준은 유지되지만 매일 ±3% 널뛰기
        values = flat_series(100.0, MA_DAYS)
        for i in range(25):
            values.append(103.0 if i % 2 == 0 else 97.0)
        result = classify_regime(make_closes(values))
        assert result["realized_vol_pct"] > 30
        assert result["regime"] == "risk_off"

    def test_shallow_pullback_above_ma_is_neutral(self):
        # 평균선 위지만 고점 대비 -7% 조정 → risk_on 조건 미달, risk_off 조건도 미달
        values = [100.0 + i * 0.2 for i in range(MA_DAYS)]
        peak = values[-1]
        values += [peak * 0.93] * 10
        result = classify_regime(make_closes(values))
        assert result["regime"] == "neutral"

    def test_insufficient_data_falls_back_to_neutral(self):
        result = classify_regime(make_closes([100.0] * 50))
        assert result["regime"] == "neutral"
        assert result.get("note") == "insufficient market data"


@pytest.mark.unit
class TestRegimeRules:
    def test_thresholds_by_regime(self):
        assert regime_rules("risk_on") == {"buy_threshold": 62, "candidate_buy_threshold": 62, "cash_floor_pct": 5.0}
        assert regime_rules("neutral") == {"buy_threshold": 65, "candidate_buy_threshold": 65, "cash_floor_pct": 5.0}
        # risk_off: 매수 기준 강화 + 신규 후보는 +5 + 현금 바닥 10%
        assert regime_rules("risk_off") == {"buy_threshold": 72, "candidate_buy_threshold": 77, "cash_floor_pct": 10.0}

    def test_unknown_regime_uses_neutral(self):
        assert regime_rules("???") == regime_rules("neutral")

    def test_constants_consistency(self):
        assert set(BUY_THRESHOLDS) == set(CASH_FLOOR_PCT) == {"risk_on", "neutral", "risk_off"}
