# graph/feedback.py
"""추천 트랙레코드: 기록 → 채점 → 스코어카드 → δ(가중치 조정) 산출.

흐름 (worker가 매 런마다 호출):
    1. score_pending_recommendations : 창(7/30/60일)이 경과한 미채점 추천을 실현 수익률로 채점
    2. (파이프라인 실행 — REVIEWER가 build_scorecard/compute_delta 사용)
    3. record_recommendations        : 이번 런의 결정을 다음 채점 대상으로 기록

채점 기준: 적중(hit)은 같은 기간 SPY 대비 초과수익의 방향으로 판정한다.
    BUY → 초과수익 > 0이면 적중 / SELL·TRIM → 초과수익 < 0이면 적중 / HOLD → 채점 제외
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from clients import get_stock_client
from data.schemas import RecommendationCreate, RecommendationOut, RecommendationReturnsPatch
from repo import get_recommendation_repo
from .agents.decider.validation import MAX_ADJUSTMENT

logger = logging.getLogger(__name__)

# 채점/δ 산출 파라미터 (Phase 4 백테스트로 튜닝 예정)
SCORING_WINDOWS = (7, 30, 60)  # 채점 창 (일)
PRIMARY_WINDOW_DAYS = 30  # 적중률/δ 판정에 쓰는 기본 창
SCORECARD_LOOKBACK_DAYS = 90  # 스코어카드 집계 기간
SIGNAL_MARGIN = 10.0  # 모멘텀/펀더멘털 "주도 콜" 판정에 필요한 점수 차이
SHRINK_TARGET_N = 20  # 이 표본 수 미만이면 δ를 비례 축소
DELTA_COEF = 0.75  # 적중률 차이 → δ 변환 계수
BENCHMARK_TICKER = "SPY"


# ---- 순수 함수: 채점 ----


def price_on_or_after(closes_by_date: Dict[date, float], target: date) -> Optional[float]:
    """target 당일 또는 그 이후 첫 거래일의 종가 (휴장일 보정)."""
    for d in sorted(closes_by_date):
        if d >= target:
            return closes_by_date[d]
    return None


def compute_returns_patch(
    rec: RecommendationOut,
    stock_closes: Dict[date, float],
    spy_closes: Dict[date, float],
    asof: date,
) -> Optional[RecommendationReturnsPatch]:
    """경과했지만 아직 채점되지 않은 창들의 수익률을 계산한다. 갱신할 것이 없으면 None."""
    fields: Dict[str, float] = {}
    rec_date = rec.created_at.date()

    for window in SCORING_WINDOWS:
        if getattr(rec, f"return_{window}d") is not None:
            continue  # 이미 채점됨
        end_date = rec_date + timedelta(days=window)
        if end_date > asof:
            continue  # 창 미경과

        stock_end = price_on_or_after(stock_closes, end_date)
        spy_start = price_on_or_after(spy_closes, rec_date)
        spy_end = price_on_or_after(spy_closes, end_date)
        if stock_end is None or spy_start is None or spy_end is None or spy_start <= 0:
            continue  # 가격 데이터 부족 — 다음 런에서 재시도

        fields[f"return_{window}d"] = round(stock_end / rec.price_at_rec - 1.0, 6)
        fields[f"benchmark_return_{window}d"] = round(spy_end / spy_start - 1.0, 6)

    return RecommendationReturnsPatch(**fields) if fields else None


def is_hit(action: str, stock_return: float, benchmark_return: float) -> Optional[bool]:
    """방향 적중 여부 (SPY 대비). HOLD는 판정 제외(None)."""
    excess = stock_return - benchmark_return
    if action == "BUY":
        return excess > 0
    if action in ("SELL", "TRIM"):
        return excess < 0
    return None


# ---- 순수 함수: 스코어카드 / δ ----


def build_scorecard(
    recs: List[RecommendationOut],
    window_days: int = PRIMARY_WINDOW_DAYS,
    asof: Optional[datetime] = None,
) -> Dict[str, Any]:
    """채점된 추천들로 적중률/초과수익 통계를 집계한다 (보고서·REVIEWER 공용)."""
    asof = asof or datetime.now(timezone.utc)
    since = asof - timedelta(days=SCORECARD_LOOKBACK_DAYS)

    scored = []  # (rec, excess, hit)
    for rec in recs:
        if rec.created_at < since:
            continue
        stock_return = getattr(rec, f"return_{window_days}d")
        benchmark_return = getattr(rec, f"benchmark_return_{window_days}d")
        if stock_return is None or benchmark_return is None:
            continue
        hit = is_hit(rec.action, stock_return, benchmark_return)
        if hit is None:
            continue
        scored.append((rec, stock_return - benchmark_return, hit))

    def summarize(subset) -> Dict[str, Any]:
        n = len(subset)
        if n == 0:
            return {"calls": 0, "hit_rate": None, "avg_excess_return_pct": None}
        hits = sum(1 for _, _, hit in subset if hit)
        avg_excess = sum(excess for _, excess, _ in subset) / n
        return {
            "calls": n,
            "hit_rate": round(hits / n, 3),
            "avg_excess_return_pct": round(avg_excess * 100, 2),
        }

    momo_led = [s for s in scored if _signal_leader(s[0]) == "momentum"]
    fund_led = [s for s in scored if _signal_leader(s[0]) == "fundamental"]

    best = max(scored, key=lambda s: s[1], default=None)
    worst = min(scored, key=lambda s: s[1], default=None)

    return {
        "window_days": window_days,
        "lookback_days": SCORECARD_LOOKBACK_DAYS,
        "overall": summarize(scored),
        "momentum_led": summarize(momo_led),
        "fundamental_led": summarize(fund_led),
        "best_call": _call_summary(best),
        "worst_call": _call_summary(worst),
    }


def compute_delta(scorecard: Dict[str, Any]) -> float:
    """스코어카드에서 MOMO/FUND 가중치 조정값 δ를 산출한다.

    δ = clamp(DELTA_COEF × (모멘텀 주도 적중률 − 펀더멘털 주도 적중률) × shrink, ±MAX_ADJUSTMENT)
    shrink = min(1, 적은 쪽 표본 수 / SHRINK_TARGET_N) — 표본이 부족하면 0으로 수축.
    """
    momo = scorecard.get("momentum_led", {})
    fund = scorecard.get("fundamental_led", {})
    if momo.get("hit_rate") is None or fund.get("hit_rate") is None:
        return 0.0

    n = min(momo["calls"], fund["calls"])
    shrink = min(1.0, n / SHRINK_TARGET_N)
    delta = DELTA_COEF * (momo["hit_rate"] - fund["hit_rate"]) * shrink
    return round(max(-MAX_ADJUSTMENT, min(MAX_ADJUSTMENT, delta)), 4)


def _signal_leader(rec: RecommendationOut) -> Optional[str]:
    """이 콜을 주도한 신호. 점수 차이가 SIGNAL_MARGIN 미만이면 양쪽 합의 콜(None)."""
    if rec.momo_score is None or rec.fund_score is None:
        return None
    if rec.momo_score >= rec.fund_score + SIGNAL_MARGIN:
        return "momentum"
    if rec.fund_score >= rec.momo_score + SIGNAL_MARGIN:
        return "fundamental"
    return None


def _call_summary(scored_item) -> Optional[Dict[str, Any]]:
    if scored_item is None:
        return None
    rec, excess, hit = scored_item
    return {"ticker": rec.ticker, "action": rec.action, "excess_return_pct": round(excess * 100, 2), "hit": hit}


# ---- 오케스트레이션 (worker / REVIEWER에서 호출) ----


async def record_recommendations(user_id: int, report_id: Optional[int], decisions: List[Dict[str, Any]]) -> int:
    """이번 런의 결정들을 트랙레코드로 기록한다. 시세가 없는 결정은 채점 불가라 제외."""
    schemas = []
    for d in decisions:
        price = float(d.get("price") or 0.0)
        if price <= 0:
            logger.warning(f"Skipping recommendation without price: {d.get('ticker')}")
            continue
        schemas.append(
            RecommendationCreate(
                user_id=user_id,
                report_id=report_id,
                ticker=d["ticker"],
                action=d["action"],
                total_score=d.get("total_score"),
                momo_score=d.get("momo_score"),
                fund_score=d.get("fund_score"),
                target_weight_pct=d.get("target_weight_pct"),
                price_at_rec=price,
                reason=d.get("reason"),
            )
        )
    saved = await get_recommendation_repo().create_many(schemas)
    return len(saved)


async def score_pending_recommendations(user_id: int, asof: Optional[datetime] = None) -> int:
    """창이 경과한 미채점 추천을 채점한다. 갱신된 추천 수를 반환."""
    asof = asof or datetime.now(timezone.utc)
    lookback = SCORECARD_LOOKBACK_DAYS + max(SCORING_WINDOWS)
    recs = await get_recommendation_repo().get_recent(user_id, days=lookback)
    if not recs:
        return 0

    spy_closes = fetch_closes(BENCHMARK_TICKER)
    if not spy_closes:
        logger.error("Benchmark price history unavailable; skipping scoring this run")
        return 0

    updated = 0
    closes_cache: Dict[str, Dict[date, float]] = {}
    for rec in recs:
        if rec.ticker not in closes_cache:
            closes_cache[rec.ticker] = fetch_closes(rec.ticker)
        patch = compute_returns_patch(rec, closes_cache[rec.ticker], spy_closes, asof.date())
        if patch is None:
            continue
        await get_recommendation_repo().update(rec.id, patch)
        updated += 1

    logger.info(f"Scored {updated} recommendations for user {user_id}")
    return updated


async def get_scorecard(user_id: int, asof: Optional[datetime] = None) -> Dict[str, Any]:
    """스코어카드 + δ 조회 (REVIEWER 에이전트용)."""
    recs = await get_recommendation_repo().get_recent(user_id, days=SCORECARD_LOOKBACK_DAYS)
    scorecard = build_scorecard(recs, asof=asof)
    scorecard["delta"] = compute_delta(scorecard)
    return scorecard


def fetch_closes(ticker: str, period: str = "6mo") -> Dict[date, float]:
    """종가 이력을 날짜→종가 dict로 변환 (휴장일 제외, 24h 캐시 적용). regime 모듈도 사용."""
    try:
        data = get_stock_client().get_stock_data([ticker], period=period)
        history = data.get("stock_history", {}).get(ticker)
        if history is None or history.empty:
            return {}
        return {idx.date(): float(close) for idx, close in history["Close"].items()}
    except Exception as e:
        logger.error(f"Failed to fetch price history for {ticker}: {e}")
        return {}
