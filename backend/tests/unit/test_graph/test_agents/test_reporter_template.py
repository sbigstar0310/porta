# tests/unit/test_graph/test_agents/test_reporter_template.py
"""Reporter 보고서 템플릿 렌더링 단위 테스트 (수치는 코드가 주입)"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from data.schemas import PortfolioOut
from graph.agents.reporter.graph import render_report


def make_decision(ticker: str, **overrides) -> dict:
    decision = {
        "ticker": ticker,
        "action": "BUY",
        "target_weight_pct": 8.5,
        "current_weight_pct": 6.0,
        "shares_to_trade": 1.5,
        "trade_value": 225.0,
        "total_score": 66.0,
        "momo_score": 70.0,
        "fund_score": 60.0,
        "reason": "fallback reason",
        "risk_notes": ["risk note 1"],
    }
    decision.update(overrides)
    return decision


@pytest.fixture
def final_portfolio() -> PortfolioOut:
    return PortfolioOut(
        id=1,
        user_id=1,
        base_currency="USD",
        cash=Decimal("150.00"),
        updated_at=datetime.now(timezone.utc),
        positions=[],
        total_stock_value=Decimal("2850.00"),
        total_value=Decimal("3000.00"),
    )


@pytest.mark.unit
class TestRenderReport:
    def test_numbers_come_from_decisions(self, final_portfolio):
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
        )
        assert "| BUY | AAPL | 8.5% | 6.0% | +1.5 | $+225.00 |" in md
        assert "66/100" in md and "모멘텀/Momentum: 70" in md

    def test_narrative_slots_rendered(self, final_portfolio):
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={
                "tldr": "핵심 요약입니다",
                "stock_comments": [{"ticker": "AAPL", "comment": "비중 확대 코멘트"}],
                "market_outlook": "- 시장 전망",
            },
        )
        assert "핵심 요약입니다" in md
        assert "비중 확대 코멘트" in md
        assert "- 시장 전망" in md

    def test_comment_falls_back_to_decision_reason(self, final_portfolio):
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
        )
        assert "fallback reason" in md

    def test_portfolio_summary_by_language(self, final_portfolio):
        kwargs = dict(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
        )
        assert "**포트폴리오 요약**: 총 가치 $3,000.00" in render_report(language="ko", **kwargs)
        assert "**Portfolio Summary**: Total value $3,000.00" in render_report(language="en", **kwargs)

    def test_renders_without_final_portfolio(self):
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL", shares_to_trade=0.0, trade_value=0.0)],
            final_portfolio=None,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
        )
        # 거래 없음은 '-'로 표시되고, 요약 라인은 생략된다
        assert "| BUY | AAPL | 8.5% | 6.0% | - | - |" in md
        assert "포트폴리오 요약" not in md

    def test_disclaimer_always_present(self, final_portfolio):
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
        )
        assert "면책사항 / Legal Disclaimer" in md

    def test_track_record_section_with_scorecard(self, final_portfolio):
        review_note = {
            "adjustment": 0.105,
            "scorecard": {
                "window_days": 30,
                "lookback_days": 90,
                "overall": {"calls": 55, "hit_rate": 0.636, "avg_excess_return_pct": 1.8},
                "momentum_led": {"calls": 30, "hit_rate": 0.70, "avg_excess_return_pct": 2.5},
                "fundamental_led": {"calls": 25, "hit_rate": 0.56, "avg_excess_return_pct": 0.9},
                "best_call": {"ticker": "NVDA", "action": "BUY", "excess_return_pct": 12.3, "hit": True},
                "worst_call": {"ticker": "XOM", "action": "BUY", "excess_return_pct": -8.1, "hit": False},
            },
        }
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
            review_note=review_note,
        )
        assert "추천 성적표 / Track Record" in md
        assert "추천 55건" in md and "적중률 64%" in md
        assert "추세 분석(모멘텀) 주도 추천 적중률 70% (30건)" in md
        assert "추세 60.5% / 기업 가치 39.5%" in md  # 50 ± δ×100
        assert "NVDA BUY (+12.3%p)" in md and "XOM BUY (-8.1%p)" in md
        assert "용어 안내" in md  # 초보자용 한 줄 설명 각주

    def test_track_record_section_without_data(self, final_portfolio):
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
            review_note={"adjustment": 0.0, "scorecard": {}},
        )
        assert "추천 성적표 / Track Record" in md
        assert "추천 성적을 쌓는 중" in md

    def test_track_record_section_in_english(self, final_portfolio):
        review_note = {
            "adjustment": 0.105,
            "scorecard": {
                "window_days": 30,
                "lookback_days": 90,
                "overall": {"calls": 55, "hit_rate": 0.636, "avg_excess_return_pct": 1.8},
                "momentum_led": {"calls": 30, "hit_rate": 0.70, "avg_excess_return_pct": 2.5},
                "fundamental_led": {"calls": 25, "hit_rate": 0.56, "avg_excess_return_pct": 0.9},
                "best_call": None,
                "worst_call": None,
            },
        }
        md = render_report(
            asof="2026-06-10T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
            language="en",
            review_note=review_note,
        )
        assert "Trend-led (momentum) calls: 70% hit rate (30 calls)" in md
        assert "Glossary" in md

    def test_market_regime_line(self, final_portfolio):
        regime = {"regime": "risk_off", "spy_vs_ma200_pct": -4.2, "drawdown_pct": -12.5, "realized_vol_pct": 32.0}
        kwargs = dict(
            asof="2026-06-11T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
            market_regime=regime,
        )
        md_ko = render_report(language="ko", **kwargs)
        assert "**시장 환경**: 위험 회피 국면 (방어 우선)" in md_ko
        assert "고점 대비 -12.5%" in md_ko
        md_en = render_report(language="en", **kwargs)
        assert "**Market Environment**: Defensive (risk-off)" in md_en

    def test_no_regime_line_when_unavailable(self, final_portfolio):
        md = render_report(
            asof="2026-06-11T09:00:00Z",
            decisions=[make_decision("AAPL")],
            final_portfolio=final_portfolio,
            narrative={"tldr": "", "stock_comments": [], "market_outlook": ""},
        )
        assert "시장 환경" not in md
