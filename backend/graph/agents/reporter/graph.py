# agents/reporter/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import ReporterOutput, ReporterState
from jinja2 import Template
from ...tools.stock_data import get_stock_data


def load_system_prompt():
    with open(
        "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "reporter/system_prompt.md",
        "r",
    ) as f:
        return Template(f.read())


REPORTER_SYSTEM_PROMPT = load_system_prompt()


def build_reporter_graph(llm_client):
    """LLM 클라이언트를 주입받는 reporter graph 빌더"""

    def agent_wrapper(state: ReporterState) -> dict:
        # tools 정의
        tools = [get_stock_data]

        # state가 dict인지 Pydantic 모델인지 확인하고 안전하게 접근
        if isinstance(state, dict):
            universe = state.get("universe", [])
            asof = state.get("asof", "")
            new_candidates = state.get("new_candidates", [])
            decisions = state.get("decisions", [])
            momo_score = state.get("momo_score", {})
            fund_score = state.get("fund_score", {})
            review_note = state.get("review_note", {})
            risk_note = state.get("risk_note", {})
            final_portfolio = state.get("final_portfolio", {})
            language = state.get("language", "ko")
        else:
            # Pydantic 모델인 경우
            asof = getattr(state, "asof", "")
            universe = getattr(state, "universe", [])
            new_candidates = getattr(state, "new_candidates", [])
            decisions = getattr(state, "decisions", [])
            momo_score = getattr(state, "momo_score", {})
            fund_score = getattr(state, "fund_score", {})
            review_note = getattr(state, "review_note", {})
            risk_note = getattr(state, "risk_note", {})
            final_portfolio = getattr(state, "final_portfolio", {})
            language = getattr(state, "language", "ko")

        # 프롬프트 렌더링
        prompt = REPORTER_SYSTEM_PROMPT.render(
            asof=asof,
            universe=universe,
            new_candidates=new_candidates,
            decisions=decisions,
            momo_score=momo_score,
            fund_score=fund_score,
            review_note=review_note,
            risk_note=risk_note,
            final_portfolio=final_portfolio,
            language=language,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=tools,
            name="reporter",
            prompt=prompt,
            response_format=ReporterOutput,
        )
        out = agent.invoke(messages=[], input=state)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            return {
                "report_md": structured_response.report_md,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "report_md": {},
            }

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
        "final_portfolio": parent.get("final_portfolio", {}),
        "language": parent.get("language", "ko"),
    }


def adapt_reporter_to_parent_out(sub_out: ReporterState) -> dict:
    report_md = sub_out.get("report_md", "")
    return {"report_md": report_md}
