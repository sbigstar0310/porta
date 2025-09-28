# agents/reporter/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from .schema import ReporterState
from jinja2 import Template
from langchain_core.runnables.config import RunnableConfig
import logging

logger = logging.getLogger(__name__)


def _last_ai_text(agent_out) -> str:
    logger.info(f"agent_out: {agent_out}")
    print(f"agent_out: {agent_out}")

    # agent_out이 dict이고 messages 키가 있는 경우
    if isinstance(agent_out, dict) and "messages" in agent_out:
        messages = agent_out["messages"]
        if messages:
            # 마지막 메시지가 AIMessage인 경우
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return last_message.content

    # 기존 로직 (generations) - 하위 호환성을 위해 유지
    if hasattr(agent_out, "generations"):
        generations = agent_out.get("generations", [])

        # get first generation output from generations
        first_generation = generations[0]
        if isinstance(first_generation, list):
            first_generation = first_generation[0]

        # get text from first generation
        if getattr(first_generation, "text", None):
            return first_generation.text

    raise ValueError("No AI text found in agent output")


def load_system_prompt():
    with open(
        "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "reporter/system_prompt.md",
        "r",
    ) as f:
        return Template(f.read())


REPORTER_SYSTEM_PROMPT = load_system_prompt()


def build_reporter_graph(llm_client):
    """LLM 클라이언트를 주입받는 reporter graph 빌더"""

    def agent_wrapper(state: ReporterState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # tools 정의
        tools = []

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
            final_portfolio = state.get("final_portfolio", None)
            language = state.get("language", "ko")
            decider_end = state.get("decider_end", False)
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
            final_portfolio = getattr(state, "final_portfolio", None)
            language = getattr(state, "language", "ko")
            decider_end = getattr(state, "decider_end", False)

        # 이전 에이전트가 끝나지 않았으면 아무 것도 하지 않음
        if not decider_end:
            return {}

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
            response_format=None,
        )
        out = agent.invoke(messages=[], input=state, config=config)

        return {
            "report_md": _last_ai_text(out),
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
        "final_portfolio": parent.get("final_portfolio", None),
        "language": parent.get("language", "ko"),
        "decider_end": parent.get("decider_end", False),
    }


def adapt_reporter_to_parent_out(sub_out: ReporterState) -> dict:
    if isinstance(sub_out, dict):
        report_md = sub_out.get("report_md", None)
    else:
        report_md = getattr(sub_out, "report_md", None)

    # 유효 값이 없으면 downstream 트리거를 만들지 않음
    if not report_md:
        return {}

    return {"report_md": report_md, "reporter_end": True}
