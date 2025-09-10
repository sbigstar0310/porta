# agents/decider/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import DeciderState, DeciderOutput
from jinja2 import Template
from ...tools.db_data import get_current_portfolio
from ...tools.stock_data import get_stock_data


def load_system_prompt():
    with open(
        "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "decider/system_prompt.md",
        "r",
    ) as f:
        return Template(f.read())


DECIDER_SYSTEM_PROMPT = load_system_prompt()


def build_decider_graph(llm_client):
    """LLM 클라이언트를 주입받는 decider graph 빌더"""

    def agent_wrapper(state: DeciderState) -> dict:
        # tools 정의
        tools = [get_current_portfolio, get_stock_data]

        # state가 dict인지 Pydantic 모델인지 확인하고 안전하게 접근
        if isinstance(state, dict):
            universe = state.get("universe", [])
            asof = state.get("asof", "")
            new_candidates = state.get("new_candidates", [])
            momo_score = state.get("momo_score", {})
            fund_score = state.get("fund_score", {})
            review_note = state.get("review_note", {})
            risk_note = state.get("risk_note", {})
        else:
            # Pydantic 모델인 경우
            universe = getattr(state, "universe", [])
            asof = getattr(state, "asof", "")
            new_candidates = getattr(state, "new_candidates", [])
            momo_score = getattr(state, "momo_score", {})
            fund_score = getattr(state, "fund_score", {})
            review_note = getattr(state, "review_note", {})
            risk_note = getattr(state, "risk_note", {})

        # 프롬프트 렌더링
        prompt = DECIDER_SYSTEM_PROMPT.render(
            universe=universe,
            asof=asof,
            new_candidates=new_candidates,
            momo_score=momo_score,
            fund_score=fund_score,
            review_note=review_note,
            risk_note=risk_note,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=tools,
            name="decider",
            prompt=prompt,
            response_format=DeciderOutput,
        )
        out = agent.invoke(messages=[], input=state)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            if isinstance(structured_response, dict):
                decisions = structured_response.get("decisions", [])
                final_portfolio = structured_response.get("final_portfolio", {})
            else:
                decisions = getattr(structured_response, "decisions", [])
                final_portfolio = getattr(structured_response, "final_portfolio", {})
            return {
                "decisions": decisions,
                "final_portfolio": final_portfolio,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "decisions": [],
                "final_portfolio": {},
            }

    g = StateGraph(DeciderState)
    g.add_node("DECIDER", agent_wrapper)
    g.add_edge(START, "DECIDER")
    g.add_edge("DECIDER", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_decider_in(parent) -> DeciderState:
    return {
        "universe": parent.get("universe", []),
        "new_candidates": parent.get("new_candidates", []),
        "momo_score": parent.get("momo_score", {}),
        "fund_score": parent.get("fund_score", {}),
        "review_note": parent.get("review_note", {}),
        "risk_note": parent.get("risk_note", {}),
        "asof": parent.get("asof"),
    }


def adapt_decider_to_parent_out(sub_out: DeciderState) -> dict:
    decisions = sub_out.get("decisions", [])
    final_portfolio = sub_out.get("final_portfolio", {})
    decisions = [d.model_dump() for d in decisions]
    final_portfolio = final_portfolio.model_dump()
    return {
        "decisions": decisions,
        "final_portfolio": final_portfolio,
    }
