# agents/fund/graph.py
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from pydantic import ValidationError
from .schema import FundState, FundItem, FundCommentaryOutput
from ...tools.stock_data import calculate_fund_scores
from ..utils import (
    apply_commentary,
    candidate_tickers,
    ensure_tool_result,
    load_template,
    run_commentary_agent,
    state_get,
)
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger(__name__)

FUND_SYSTEM_PROMPT = load_template(__file__)


def _parse_fund_items(tool_result: dict) -> list[FundItem]:
    """도구 원본 결과(`scores` 키)를 FundItem으로 검증."""
    items = []
    for raw in tool_result.get("scores", []):
        try:
            items.append(FundItem.model_validate(raw))
        except ValidationError as e:
            logger.warning(f"Skipping invalid fund result for {raw.get('ticker')}: {e}")
    return items


def build_fund_graph(llm_client):
    """LLM 클라이언트를 주입받는 fund graph 빌더"""

    def agent_wrapper(state: FundState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        universe = state_get(state, "universe", [])
        new_candidates = state_get(state, "new_candidates", [])

        prompt = FUND_SYSTEM_PROMPT.render(
            universe=universe,
            asof=state_get(state, "asof", ""),
            new_candidates=new_candidates,
        )

        # LLM 출력은 해석(commentary)만 받고, 숫자는 ToolMessage 원본에서 읽는다
        agent = create_react_agent(
            model=llm_client,
            tools=[calculate_fund_scores],
            name="fund",
            prompt=prompt,
            response_format=FundCommentaryOutput,
        )
        tool_result, commentary = run_commentary_agent(agent, state, config, tool_name="calculate_fund_scores")
        tool_result = ensure_tool_result(
            tool_result,
            calculate_fund_scores,
            result_key="scores",
            tickers=candidate_tickers(universe, new_candidates),
        )
        if tool_result is None:
            logger.error("Fund score calculation failed")
            return {"fund_score": []}

        fund_items = _parse_fund_items(tool_result)
        apply_commentary(fund_items, commentary)
        return {"fund_score": fund_items}

    g = StateGraph(FundState)
    g.add_node("FUND", agent_wrapper)
    g.add_edge(START, "FUND")
    g.add_edge("FUND", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_fund_in(parent) -> FundState:
    return {
        "asof": parent.get("asof"),
        "universe": parent.get("universe", []),
        "new_candidates": parent.get("new_candidates", []),
    }


def adapt_fund_to_parent_out(sub_out: FundState) -> dict:
    fund_score = sub_out.get("fund_score", [])
    fund_score = [f_item.model_dump() for f_item in fund_score]
    return {"fund_score": fund_score, "fund_end": True}
