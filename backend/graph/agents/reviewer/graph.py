# agents/reviewer/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import ReviewerState, ReviewerOutput
from jinja2 import Template
from ...tools.db_data import get_portfolio_history
from ...tools.stock_data import get_benchmark_data
from langchain_core.runnables.config import RunnableConfig


def load_system_prompt():
    with open(
        "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "reviewer/system_prompt.md",
        "r",
    ) as f:
        return Template(f.read())


REVIEWER_SYSTEM_PROMPT = load_system_prompt()


def build_reviewer_graph(llm_client):
    """LLM 클라이언트를 주입받는 reviewer graph 빌더"""

    def agent_wrapper(state: ReviewerState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # tools 정의 - 포트폴리오 기록과 벤치마크 데이터 가져오기
        tools = [get_portfolio_history, get_benchmark_data]

        # state가 dict인지 Pydantic 모델인지 확인하고 안전하게 접근
        if isinstance(state, dict):
            universe = state.get("universe", [])
            asof = state.get("asof", "")
        else:
            # Pydantic 모델인 경우
            universe = getattr(state, "universe", [])
            asof = getattr(state, "asof", "")

        # 프롬프트 렌더링
        prompt = REVIEWER_SYSTEM_PROMPT.render(
            universe=universe,
            asof=asof,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=tools,
            name="reviewer",
            prompt=prompt,
            response_format=ReviewerOutput,
        )
        out = agent.invoke(messages=[], input=state, config=config)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            if isinstance(structured_response, dict):
                review_note = structured_response.get("review_note", {})
            else:
                review_note = getattr(structured_response, "review_note", {})
            return {
                "review_note": review_note,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "review_note": {},
            }

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
    review_note = sub_out.get("review_note", {})
    review_note = review_note.model_dump()
    return {"review_note": review_note, "review_end": True}
