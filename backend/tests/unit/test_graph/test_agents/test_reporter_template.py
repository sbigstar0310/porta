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
