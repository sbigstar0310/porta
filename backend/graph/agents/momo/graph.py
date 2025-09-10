# agents/momo/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import MomoState, MomoOutput
from jinja2 import Template
from ...tools.stock_data import calculate_momentum_scores


def load_system_prompt():
    with open(
        "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "momo/system_prompt.md",
        "r",
    ) as f:
        return Template(f.read())


MOMO_SYSTEM_PROMPT = load_system_prompt()


def build_momo_graph(llm_client):
    """LLM 클라이언트를 주입받는 momo graph 빌더"""

    def agent_wrapper(state: MomoState) -> dict:
        # tools 정의 - 통합된 모멘텀 스코어 계산 도구
        tools = [calculate_momentum_scores]

        # state가 dict인지 Pydantic 모델인지 확인하고 안전하게 접근
        if isinstance(state, dict):
            asof = state.get("asof", "")
            universe = state.get("universe", [])
            new_candidates = state.get("new_candidates", [])
        else:
            # Pydantic 모델인 경우
            asof = getattr(state, "asof", "")
            universe = getattr(state, "universe", [])
            new_candidates = getattr(state, "new_candidates", [])

        # 프롬프트 렌더링
        prompt = MOMO_SYSTEM_PROMPT.render(
            universe=universe,
            asof=asof,
            new_candidates=new_candidates,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=tools,
            name="momo",
            prompt=prompt,
            response_format=MomoOutput,
        )
        out = agent.invoke(messages=[], input=state)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            if isinstance(structured_response, dict):
                momo_score = structured_response.get("momo_score", [])
            else:
                momo_score = getattr(structured_response, "momo_score", [])
            return {
                "momo_score": momo_score,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "momo_score": [],
            }

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
    return {"momo_score": momo_score}
