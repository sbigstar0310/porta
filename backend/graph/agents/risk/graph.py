# agents/risk/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

from ...tools.stock_data import calculate_max_weight_pct, get_stock_data
from ...tools.db_data import get_current_portfolio
from .schema import RiskOutput, RiskState
from jinja2 import Template


def load_system_prompt():
    prompt_path = "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "risk/system_prompt.md"
    with open(prompt_path, "r") as f:
        return Template(f.read())


RISK_SYSTEM_PROMPT = load_system_prompt()


def build_risk_graph(llm_client):
    """LLM 클라이언트를 주입받는 risk graph 빌더"""

    def agent_wrapper(state: RiskState) -> dict:
        # tools 정의
        tools = [get_current_portfolio, calculate_max_weight_pct, get_stock_data]

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
        prompt = RISK_SYSTEM_PROMPT.render(
            universe=universe,
            asof=asof,
            new_candidates=new_candidates,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=tools,
            name="risk",
            prompt=prompt,
            response_format=RiskOutput,
        )
        out = agent.invoke(messages=[], input=state)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            if isinstance(structured_response, dict):
                risk_note = structured_response.get("risk_note", {})
            else:
                risk_note = getattr(structured_response, "risk_note", {})
            return {
                "risk_note": risk_note,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "risk_note": {},
            }

    g = StateGraph(RiskState)
    g.add_node("RISK", agent_wrapper)
    g.add_edge(START, "RISK")
    g.add_edge("RISK", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_risk_in(parent) -> RiskState:
    return {
        "asof": parent.get("asof"),
        "universe": parent.get("universe", []),
        "new_candidates": parent.get("new_candidates", []),
        "momo_score": parent.get("momo_score", []),
        "fund_score": parent.get("fund_score", []),
    }


def adapt_risk_to_parent_out(sub_out: RiskState) -> dict:
    risk_note = sub_out.get("risk_note", {})
    risk_note = risk_note.model_dump()
    return {"risk_note": risk_note}
