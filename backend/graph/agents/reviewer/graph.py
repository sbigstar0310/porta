# agents/reviewer/graph.py
import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import ReviewerState, ReviewerNote, ReviewerNarrative
from ...feedback import SCORECARD_LOOKBACK_DAYS, get_scorecard
from ...tools.db_data import get_portfolio_history
from ...tools.stock_data import get_benchmark_data
from ..utils import extract_structured_response, load_template, state_get
from langchain_core.runnables.config import RunnableConfig

logger = logging.getLogger(__name__)

REVIEWER_SYSTEM_PROMPT = load_template(__file__)

# preference 판정 기준: |δ|가 이 값 이상일 때만 한쪽 신호 선호로 표기
PREFERENCE_THRESHOLD = 0.02


def _preference(delta: float) -> str:
    if delta >= PREFERENCE_THRESHOLD:
        return "momentum"
    if delta <= -PREFERENCE_THRESHOLD:
        return "fundamental"
    return "balanced"


def build_reviewer_graph(llm_client):
    """LLM 클라이언트를 주입받는 reviewer graph 빌더"""

    def agent_wrapper(state: ReviewerState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        user_id = state_get(state, "user_id", 0)
        asof = state_get(state, "asof", "")

        # δ와 통계는 트랙레코드에서 코드가 계산한다 (LLM은 해석만)
        try:
            scorecard = asyncio.run(get_scorecard(user_id))
        except Exception as e:
            logger.error(f"Failed to build scorecard for user {user_id}: {e}")
            scorecard = {}
        delta = float(scorecard.get("delta", 0.0))
        preference = _preference(delta)

        prompt = REVIEWER_SYSTEM_PROMPT.render(
            asof=asof,
            scorecard=scorecard,
            delta=delta,
            preference=preference,
        )
        agent = create_react_agent(
            model=llm_client,
            tools=[get_portfolio_history, get_benchmark_data],
            name="reviewer",
            prompt=prompt,
            response_format=ReviewerNarrative,
        )

        opinion = ""
        try:
            out = agent.invoke(messages=[], input=state, config=config)
            opinion = extract_structured_response(out).get("opinion", "")
        except Exception as e:
            logger.error(f"Reviewer LLM invocation failed; continuing with stats only: {e}")

        review_note = ReviewerNote(
            period=f"최근 {SCORECARD_LOOKBACK_DAYS}일",
            opinion=opinion,
            preference=preference,
            adjustment=delta,
            scorecard=scorecard,
        )
        return {"review_note": review_note}

    g = StateGraph(ReviewerState)
    g.add_node("REVIEWER", agent_wrapper)
    g.add_edge(START, "REVIEWER")
    g.add_edge("REVIEWER", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_reviewer_in(parent) -> ReviewerState:
    return {
        "user_id": parent.get("user_id", 1),
        "asof": parent.get("asof"),
    }


def adapt_reviewer_to_parent_out(sub_out: ReviewerState) -> dict:
    review_note = state_get(sub_out, "review_note")
    if review_note is None:
        return {"review_note": {}, "review_end": True}
    if hasattr(review_note, "model_dump"):
        review_note = review_note.model_dump()
    return {"review_note": review_note, "review_end": True}
