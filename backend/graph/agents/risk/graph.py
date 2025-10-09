# agents/risk/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

from ...tools.stock_data import calculate_max_weight_pct, get_stock_data
from ...tools.db_data import get_current_portfolio
from .schema import RiskOutput, RiskState
from jinja2 import Template
from langchain_core.runnables.config import RunnableConfig


def load_system_prompt():
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "system_prompt.md")
    with open(prompt_path, "r") as f:
        return Template(f.read())


RISK_SYSTEM_PROMPT = load_system_prompt()


def build_risk_graph(llm_client):
    """LLM 클라이언트를 주입받는 risk graph 빌더"""

    def agent_wrapper(state: RiskState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # tools 정의
        tools = [get_current_portfolio, calculate_max_weight_pct, get_stock_data]

        # state가 dict인지 Pydantic 모델인지 확인하고 안전하게 접근
        if isinstance(state, dict):
            asof = state.get("asof", "")
            universe = state.get("universe", [])
            new_candidates = state.get("new_candidates", [])
            risk_end = state.get("risk_end", False)
            momo_end = state.get("momo_end", False)
            fund_end = state.get("fund_end", False)
            review_end = state.get("review_end", False)
        else:
            # Pydantic 모델인 경우
            asof = getattr(state, "asof", "")
            universe = getattr(state, "universe", [])
            new_candidates = getattr(state, "new_candidates", [])
            risk_end = getattr(state, "risk_end", False)
            momo_end = getattr(state, "momo_end", False)
            fund_end = getattr(state, "fund_end", False)
            review_end = getattr(state, "review_end", False)

        # 이미 끝났으면 아무 것도 하지 않음 (downstream 트리거 X)
        if risk_end:
            return {}

        # 아직 이전 에이전트들의 입력 안 모임 → 상태 미변경 (downstream 트리거 X)
        if not (momo_end and fund_end and review_end):
            return {}

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
        out = agent.invoke(messages=[], input=state, config=config)

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
            return {}

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
        "momo_end": parent.get("momo_end", False),
        "fund_end": parent.get("fund_end", False),
        "review_end": parent.get("review_end", False),
        "risk_end": parent.get("risk_end", False),
    }


def adapt_risk_to_parent_out(sub_out: RiskState) -> dict:
    if isinstance(sub_out, dict):
        risk_note = sub_out.get("risk_note", {})
    else:
        risk_note = getattr(sub_out, "risk_note", {})

    # pydantic or dict 안전 처리
    if hasattr(risk_note, "model_dump"):
        risk_note = risk_note.model_dump()
    else:
        risk_note = dict(risk_note) if risk_note else {}

    # 유효 값이 없으면 downstream 트리거를 만들지 않음
    if not risk_note:
        return {}

    return {"risk_note": risk_note, "risk_end": True}
