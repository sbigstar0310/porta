# agents/fund/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import FundOutput, FundState
from jinja2 import Template
from ...tools.stock_data import calculate_fund_scores
from langchain_core.runnables.config import RunnableConfig


def load_system_prompt():
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "system_prompt.md")
    with open(prompt_path, "r") as f:
        return Template(f.read())


FUND_SYSTEM_PROMPT = load_system_prompt()


def build_fund_graph(llm_client):
    """LLM 클라이언트를 주입받는 fund graph 빌더"""

    def agent_wrapper(state: FundState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # tools 정의 - 통합된 모멘텀 스코어 계산 도구
        tools = [calculate_fund_scores]

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
        prompt = FUND_SYSTEM_PROMPT.render(
            universe=universe,
            asof=asof,
            new_candidates=new_candidates,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=tools,
            name="fund",
            prompt=prompt,
            response_format=FundOutput,
        )
        out = agent.invoke(messages=[], input=state, config=config)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            if isinstance(structured_response, dict):
                fund_score = structured_response.get("fund_score", [])
            else:
                fund_score = getattr(structured_response, "fund_score", [])
            return {
                "fund_score": fund_score,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "fund_score": [],
            }

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
