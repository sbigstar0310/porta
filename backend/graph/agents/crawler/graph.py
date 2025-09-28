# agents/crawler/graph.py
from langgraph.graph import StateGraph, START, END
from .schema import CrawlerOutput, CrawlerState
from ...schemas import ParentState
from datetime import datetime
from jinja2 import Template
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.runnables.config import RunnableConfig


def load_system_prompt():
    with open(
        "/Users/sbigstar/Desktop/Projects/porta/backend/graph/agents/" "crawler/system_prompt.md",
        "r",
    ) as f:
        return Template(f.read())


CRAWLER_SYSTEM_PROMPT = load_system_prompt()


def build_crawler_graph(llm_client):
    """LLM 클라이언트를 주입받아 create_react_agent로 간단 구성"""

    def agent_wrapper(state: CrawlerState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        # Pre-built DuckDuckGo 툴 생성
        web_search_tool = DuckDuckGoSearchResults()

        # state가 dict인지 Pydantic 모델인지 확인하고 안전하게 접근
        if isinstance(state, dict):
            universe = state.get("universe", [])
            asof = state.get("asof", "")
        else:
            # Pydantic 모델인 경우
            universe = getattr(state, "universe", [])
            asof = getattr(state, "asof", "")

        # 프롬프트 렌더링
        prompt = CRAWLER_SYSTEM_PROMPT.render(
            universe=universe,
            asof=asof,
        )

        # 에이전트 생성
        agent = create_react_agent(
            model=llm_client,
            tools=[web_search_tool],
            name="crawler",
            prompt=prompt,
            response_format=CrawlerOutput,
        )
        out = agent.invoke(messages=[], input=state, config=config)

        # structured_response에서 실제 결과 추출
        if "structured_response" in out and out["structured_response"]:
            structured_response = out["structured_response"]
            if isinstance(structured_response, dict):
                new_candidates = structured_response.get("new_candidates", [])
            else:
                new_candidates = getattr(structured_response, "new_candidates", [])
            return {
                "new_candidates": new_candidates,
            }
        else:
            # 폴백: 빈 결과 반환
            return {
                "new_candidates": [],
            }

    g = StateGraph(CrawlerState)
    g.add_node("CRAWLER", agent_wrapper)  # wrapper 함수를 전달
    g.add_edge(START, "CRAWLER")
    g.add_edge("CRAWLER", END)
    return g.compile()


# ---- 부모<->자식 어댑터 ----
def adapt_parent_to_crawler_in(parent: ParentState) -> CrawlerState:
    return {
        "universe": parent.get("universe", []),
        "asof": parent.get("asof"),
    }


def adapt_crawler_to_parent_out(sub_out: CrawlerState) -> dict:
    snapshot_id = "crawl_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    new_candidates = sub_out.get("new_candidates", [])
    new_candidates = [c.model_dump() for c in new_candidates]
    return {
        "crawl_snapshot_id": snapshot_id,
        "new_candidates": new_candidates,
        "crawler_end": True,
    }
