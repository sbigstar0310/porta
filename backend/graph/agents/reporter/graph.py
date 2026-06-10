# agents/reporter/graph.py
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import ReporterState, ReporterNarrative
from ..utils import extract_structured_response, load_template, state_get
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger(__name__)

REPORTER_SYSTEM_PROMPT = load_template(__file__)
REPORT_TEMPLATE = load_template(__file__, "report_template.md")

EMPTY_NARRATIVE = {"tldr": "", "stock_comments": [], "market_outlook": ""}

REGIME_LABELS = {
    "ko": {"risk_on": "안정 상승 국면", "neutral": "중립 국면", "risk_off": "위험 회피 국면 (방어 우선)"},
    "en": {"risk_on": "Supportive (risk-on)", "neutral": "Neutral", "risk_off": "Defensive (risk-off)"},
}


def render_report(
    asof: str,
    decisions: list,
    final_portfolio,
    narrative: dict,
    language: str = "ko",
    review_note: dict | None = None,
    market_regime: dict | None = None,
) -> str:
    """보고서 골격과 모든 수치는 코드가 렌더링하고, LLM 서술은 지정 슬롯에만 들어간다."""
    comments = {c.get("ticker"): c.get("comment") for c in narrative.get("stock_comments", []) if isinstance(c, dict)}
    market_regime = market_regime or {}
    labels = REGIME_LABELS.get(language, REGIME_LABELS["ko"])
    return REPORT_TEMPLATE.render(
        asof=asof,
        decisions=decisions,
        final_portfolio=final_portfolio,
        narrative=narrative,
        comments=comments,
        language=language,
        review_note=review_note or {},
        market_regime=market_regime,
        regime_label=labels.get(market_regime.get("regime")),
    )


def build_reporter_graph(llm_client):
    """LLM 클라이언트를 주입받는 reporter graph 빌더"""

    def agent_wrapper(state: ReporterState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # 이전 에이전트가 끝나지 않았으면 아무 것도 하지 않음
        if not state_get(state, "decider_end", False):
            return {}

        asof = state_get(state, "asof", "")
        decisions = state_get(state, "decisions", [])
        final_portfolio = state_get(state, "final_portfolio")
        language = state_get(state, "language", "ko")
        review_note = state_get(state, "review_note", {})
        market_regime = state_get(state, "market_regime", {})

        prompt = REPORTER_SYSTEM_PROMPT.render(
            asof=asof,
            universe=state_get(state, "universe", []),
            new_candidates=state_get(state, "new_candidates", []),
            decisions=decisions,
            momo_score=state_get(state, "momo_score", []),
            fund_score=state_get(state, "fund_score", []),
            review_note=review_note,
            risk_note=state_get(state, "risk_note", {}),
            final_portfolio=final_portfolio,
            language=language,
        )

        # LLM 출력은 서술(narrative)만 받는다. 실패해도 수치 테이블은 항상 렌더링된다.
        agent = create_react_agent(
            model=llm_client,
            tools=[],
            name="reporter",
            prompt=prompt,
            response_format=ReporterNarrative,
        )
        try:
            out = agent.invoke(messages=[], input=state, config=config)
            narrative = {**EMPTY_NARRATIVE, **extract_structured_response(out)}
        except Exception as e:
            logger.error(f"Reporter LLM invocation failed; rendering report without prose: {e}")
            narrative = EMPTY_NARRATIVE

        report_md = render_report(
            asof, decisions, final_portfolio, narrative, language,
            review_note=review_note, market_regime=market_regime,
        )
        return {"report_md": report_md}

    g = StateGraph(ReporterState)
    g.add_node("REPORTER", agent_wrapper)
    g.add_edge(START, "REPORTER")
    g.add_edge("REPORTER", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_reporter_in(parent) -> ReporterState:
    return {
        "asof": parent.get("asof"),
        "universe": parent.get("universe", []),
        "new_candidates": parent.get("new_candidates", []),
        "decisions": parent.get("decisions", []),
        "momo_score": parent.get("momo_score", {}),
        "fund_score": parent.get("fund_score", {}),
        "review_note": parent.get("review_note", {}),
        "risk_note": parent.get("risk_note", {}),
        "final_portfolio": parent.get("final_portfolio", None),
        "market_regime": parent.get("market_regime", {}),
        "language": parent.get("language", "ko"),
        "decider_end": parent.get("decider_end", False),
    }


def adapt_reporter_to_parent_out(sub_out: ReporterState) -> dict:
    report_md = state_get(sub_out, "report_md")

    # 유효 값이 없으면 downstream 트리거를 만들지 않음
    if not report_md:
        return {}

    return {"report_md": report_md, "reporter_end": True}
