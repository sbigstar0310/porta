# tests/unit/test_graph/test_feedback.py
"""추천 트랙레코드(graph/feedback.py) 순수 함수 단위 테스트"""
import pytest
from datetime import date, datetime, timedelta, timezone

from data.schemas import RecommendationOut
from graph.feedback import (
    DELTA_COEF,
    SHRINK_TARGET_N,
    build_scorecard,
    compute_delta,
    compute_returns_patch,
    is_hit,
    price_on_or_after,
)
from graph.agents.decider.validation import MAX_ADJUSTMENT

NOW = datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc)


def make_rec(
    ticker: str = "AAPL",
    action: str = "BUY",
    days_ago: int = 40,
    momo: float = None,
    fund: float = None,
    rec_id: int = 1,
    price_at_rec: float = 100.0,
    **scoring,
) -> RecommendationOut:
    return RecommendationOut(
        id=rec_id,
        user_id=1,
        ticker=ticker,
        action=action,
        momo_score=momo,
        fund_score=fund,
        price_at_rec=price_at_rec,
        created_at=NOW - timedelta(days=days_ago),
        **scoring,
    )


@pytest.mark.unit
class TestPriceOnOrAfter:
    closes = {date(2026, 5, 1): 100.0, date(2026, 5, 4): 102.0, date(2026, 5, 5): 104.0}

    def test_exact_date(self):
        assert price_on_or_after(self.closes, date(2026, 5, 4)) == 102.0

    def test_skips_non_trading_days(self):
        # 5/2(토)~5/3(일) 휴장 → 다음 거래일 5/4 종가
        assert price_on_or_after(self.closes, date(2026, 5, 2)) == 102.0

    def test_none_beyond_data(self):
        assert price_on_or_after(self.closes, date(2026, 5, 6)) is None


@pytest.mark.unit
class TestIsHit:
    def test_buy_hit_when_beats_benchmark(self):
        assert is_hit("BUY", 0.10, 0.05) is True
        assert is_hit("BUY", 0.03, 0.05) is False  # 절대수익 +여도 시장에 졌으면 미적중

    def test_sell_hit_when_underperforms(self):
        assert is_hit("SELL", -0.02, 0.05) is True  # 잘 피함
        assert is_hit("TRIM", 0.10, 0.05) is False  # 판 게 시장을 이겼으면 미적중

    def test_hold_excluded(self):
        assert is_hit("HOLD", 0.10, 0.05) is None


@pytest.mark.unit
class TestComputeReturnsPatch:
    @pytest.fixture
    def histories(self):
        """추천일(40일 전)부터 일별 종가: 주식은 일정 상승, SPY는 완만 상승"""
        rec_date = (NOW - timedelta(days=40)).date()
        stock, spy = {}, {}
        for i in range(0, 41):
            d = rec_date + timedelta(days=i)
            stock[d] = 100.0 + i  # 7일 후 107, 30일 후 130
            spy[d] = 400.0 + i * 0.4  # 7일 후 402.8, 30일 후 412
        return stock, spy

    def test_scores_elapsed_windows_only(self, histories):
        stock, spy = histories
        rec = make_rec(days_ago=40)  # 7d/30d 경과, 60d 미경과
        patch = compute_returns_patch(rec, stock, spy, NOW.date())
        assert patch.return_7d == pytest.approx(0.07)
        assert patch.return_30d == pytest.approx(0.30)
        assert patch.return_60d is None
        assert patch.benchmark_return_7d == pytest.approx(402.8 / 400 - 1, abs=1e-4)
        assert patch.benchmark_return_30d == pytest.approx(412 / 400 - 1, abs=1e-4)

    def test_skips_already_scored_windows(self, histories):
        stock, spy = histories
        rec = make_rec(days_ago=40, return_7d=0.07, benchmark_return_7d=0.007)
        patch = compute_returns_patch(rec, stock, spy, NOW.date())
        assert patch.return_7d is None  # 갱신 대상 아님
        assert patch.return_30d is not None

    def test_none_when_nothing_to_score(self, histories):
        stock, spy = histories
        rec = make_rec(days_ago=3)  # 어떤 창도 미경과
        assert compute_returns_patch(rec, stock, spy, NOW.date()) is None

    def test_none_when_prices_missing(self):
        rec = make_rec(days_ago=40)
        assert compute_returns_patch(rec, {}, {}, NOW.date()) is None


@pytest.mark.unit
class TestBuildScorecard:
    def scored_rec(self, ticker, action, momo, fund, ret, bench, days_ago=40, rec_id=1):
        return make_rec(
            ticker=ticker,
            action=action,
            momo=momo,
            fund=fund,
            days_ago=days_ago,
            rec_id=rec_id,
            return_30d=ret,
            benchmark_return_30d=bench,
        )

    def test_aggregates_and_classifies_by_signal_leader(self):
        recs = [
            self.scored_rec("AAPL", "BUY", momo=75, fund=50, ret=0.10, bench=0.02, rec_id=1),  # 모멘텀 주도, 적중
            self.scored_rec("MSFT", "BUY", momo=72, fund=55, ret=-0.05, bench=0.02, rec_id=2),  # 모멘텀 주도, 미적중
            self.scored_rec("KO", "BUY", momo=50, fund=70, ret=0.08, bench=0.02, rec_id=3),  # 펀더멘털 주도, 적중
            self.scored_rec("JNJ", "BUY", momo=66, fund=64, ret=0.09, bench=0.02, rec_id=4),  # 합의 콜 → 분류 제외
            self.scored_rec("XOM", "HOLD", momo=75, fund=50, ret=0.10, bench=0.02, rec_id=5),  # HOLD → 전체 제외
            make_rec(ticker="NEW", days_ago=10, rec_id=6),  # 미채점 → 제외
        ]
        sc = build_scorecard(recs, asof=NOW)
        assert sc["overall"]["calls"] == 4  # HOLD/미채점 제외
        assert sc["momentum_led"]["calls"] == 2
        assert sc["momentum_led"]["hit_rate"] == 0.5
        assert sc["fundamental_led"]["calls"] == 1
        assert sc["fundamental_led"]["hit_rate"] == 1.0
        assert sc["best_call"]["ticker"] == "AAPL"
        assert sc["worst_call"]["ticker"] == "MSFT"

    def test_excludes_recs_older_than_lookback(self):
        recs = [self.scored_rec("OLD", "BUY", momo=75, fund=50, ret=0.10, bench=0.02, days_ago=120)]
        sc = build_scorecard(recs, asof=NOW)
        assert sc["overall"]["calls"] == 0
        assert sc["overall"]["hit_rate"] is None


@pytest.mark.unit
class TestComputeDelta:
    def scorecard(self, momo_calls, momo_hr, fund_calls, fund_hr):
        return {
            "momentum_led": {"calls": momo_calls, "hit_rate": momo_hr},
            "fundamental_led": {"calls": fund_calls, "hit_rate": fund_hr},
        }

    def test_full_sample_delta(self):
        # 표본 충분(양쪽 ≥ SHRINK_TARGET_N) → δ = 0.75 × (0.70 − 0.56)
        sc = self.scorecard(30, 0.70, 25, 0.56)
        assert compute_delta(sc) == pytest.approx(DELTA_COEF * 0.14, abs=1e-4)

    def test_clamped_at_max_adjustment(self):
        sc = self.scorecard(30, 0.90, 25, 0.30)  # 0.75 × 0.6 = 0.45 → 클램프
        assert compute_delta(sc) == MAX_ADJUSTMENT

    def test_shrinks_with_small_sample(self):
        sc = self.scorecard(30, 0.70, 8, 0.56)  # 적은 쪽 8건 → shrink 8/20
        expected = DELTA_COEF * 0.14 * (8 / SHRINK_TARGET_N)
        assert compute_delta(sc) == pytest.approx(expected, abs=1e-4)

    def test_zero_without_evidence(self):
        assert compute_delta(self.scorecard(0, None, 25, 0.56)) == 0.0
        assert compute_delta({}) == 0.0

    def test_negative_delta_favors_fundamental(self):
        sc = self.scorecard(25, 0.50, 25, 0.66)
        assert compute_delta(sc) == pytest.approx(-DELTA_COEF * 0.16, abs=1e-4)