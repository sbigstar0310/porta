# agents/momo/graph.py
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from pydantic import ValidationError
from .schema import MomoState, MomoItem, MomoCommentaryOutput
from ...tools.stock_data import calculate_momentum_scores
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

MOMO_SYSTEM_PROMPT = load_template(__file__)


def _parse_momo_items(tool_result: dict) -> list[MomoItem]:
    """도구 원본 결과를 MomoItem으로 검증. 정규화 점수 결측은 0.0으로 채운다."""
    items = []
    for raw in tool_result.get("momo_score", []):
        score = raw.get("score", {})
        norm = {k: v for k, v in score.get("norm", {}).items() if v is not None}
        score["norm"] = {"z20": 0.0, "z60": 0.0, "zvol": 0.0, **norm}
        try:
            items.append(MomoItem.model_validate({"ticker": raw.get("ticker"), "score": score}))
        except ValidationError as e:
            logger.warning(f"Skipping invalid momo result for {raw.get('ticker')}: {e}")
    return items


def build_momo_graph(llm_client):
    """LLM 클라이언트를 주입받는 momo graph 빌더"""

    def agent_wrapper(state: MomoState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        universe = state_get(state, "universe", [])
        new_candidates = state_get(state, "new_candidates", [])

        prompt = MOMO_SYSTEM_PROMPT.render(
            universe=universe,
            asof=state_get(state, "asof", ""),
            new_candidates=new_candidates,
        )

        # LLM 출력은 해석(commentary)만 받고, 숫자는 ToolMessage 원본에서 읽는다
        agent = create_react_agent(
            model=llm_client,
            tools=[calculate_momentum_scores],
            name="momo",
            prompt=prompt,
            response_format=MomoCommentaryOutput,
        )
        tool_result, commentary = run_commentary_agent(agent, state, config, tool_name="calculate_momentum_scores")
        tool_result = ensure_tool_result(
            tool_result,
            calculate_momentum_scores,
            result_key="momo_score",
            tickers=candidate_tickers(universe, new_candidates),
        )
        if tool_result is None:
            logger.error("Momentum score calculation failed")
            return {"momo_score": []}

        momo_items = _parse_momo_items(tool_result)
        apply_commentary(momo_items, commentary)
        return {"momo_score": momo_items}

    g = StateGraph(MomoState)
    g.add_node("MOMO", agent_wrapper)
    g.add_edge(START, "MOMO")
    g.add_edge("MOMO", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_momo_in(parent) -> MomoState:
    return {
        "asof": parent.get("asof"),
        "universe": parent.get("universe", []),
        "new_candidates": parent.get("new_candidates", []),
    }


def adapt_momo_to_parent_out(sub_out: MomoState) -> dict:
    momo_score = sub_out.get("momo_score", [])
    momo_score = [m_item.model_dump() for m_item in momo_score]
    return {"momo_score": momo_score, "momo_end": True}
