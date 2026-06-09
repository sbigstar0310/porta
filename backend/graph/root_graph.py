# graph/root_graph.py
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables.config import RunnableConfig
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy
from .schemas import ParentState
from .agents.crawler.graph import (
    build_crawler_graph,
    adapt_parent_to_crawler_in,
    adapt_crawler_to_parent_out,
)
from .agents.momo.graph import (
    build_momo_graph,
    adapt_parent_to_momo_in,
    adapt_momo_to_parent_out,
)
from .agents.fund.graph import (
    build_fund_graph,
    adapt_parent_to_fund_in,
    adapt_fund_to_parent_out,
)
from .agents.reviewer.graph import (
    build_reviewer_graph,
    adapt_parent_to_reviewer_in,
    adapt_reviewer_to_parent_out,
)
from .agents.risk.graph import (
    build_risk_graph,
    adapt_parent_to_risk_in,
    adapt_risk_to_parent_out,
)
from .agents.decider.graph import (
    build_decider_graph,
    adapt_parent_to_decider_in,
    adapt_decider_to_parent_out,
)
from .agents.reporter.graph import (
    build_reporter_graph,
    adapt_parent_to_reporter_in,
    adapt_reporter_to_parent_out,
)
from .llm_clients.openai_client import LLMTier, get_openai_client
import json


# 에이전트별 모델 tier. 한 줄만 바꾸면 해당 에이전트의 모델이 바뀐다.
# (tier → 실제 모델명 매핑은 llm_clients/openai_client.py:TIER_MODELS 참고)
# 배분 근거: 계산을 툴에 위임하거나 저stakes인 에이전트는 가벼운 tier,
# 실제 판단(DECIDER)·사용자 대면 산출물(REPORTER)에만 최상위 tier를 쓴다.
AGENT_TIERS: dict[str, LLMTier] = {
    "CRAWLER": LLMTier.MIDDLE,  # 뉴스/후보 발굴 — 검색+요약, 하류 재채점으로 자정 (gpt-5.4-mini)
    "MOMO": LLMTier.LIGHT,      # 모멘텀 — 툴이 전부 계산, LLM은 포맷터 (gpt-5.4-nano)
    "FUND": LLMTier.MIDDLE,     # 펀더멘털 — 툴이 점수 계산, 인사이트만 서술 (gpt-5.4-mini)
    "REVIEWER": LLMTier.LIGHT,  # 과거 성과 리뷰 — 저stakes, 대부분 디폴트 (gpt-5.4-nano)
    "RISK": LLMTier.MIDDLE,     # 리스크 — 명시적 규칙/공식 실행, 입력 최대 (gpt-5.4-mini)
    "DECIDER": LLMTier.MIDDLE,  # 최종 매수/매도/수량 — 판단 핵심이나 입력 100K라 heavy는 비효율, gpt-5.4-mini로 (gpt-5.4-mini)
    "REPORTER": LLMTier.MIDDLE, # 사용자 대면 리포트 작성 — gpt-5.4-mini로 충분, 비용 절감 (gpt-5.4-mini)
}


def node_subgraph(subgraph, inbound, outbound):
    """부모↔자식 어댑터 래퍼 (config 전파 지원)"""

    def _call(state: ParentState, *, config: RunnableConfig | None = None, **kwargs) -> dict:
        sub_in = inbound(state)
        sub_out = subgraph.invoke(sub_in, config=config)
        return outbound(sub_out)

    return _call


def crawler_cache_key(node_input: dict) -> str:
    """
    CRAWLER 입력에서 캐시 키로 쓰일 핵심만 추출해 안정적으로 직렬화.
    - asof는 'YYYY-MM-DD'로 내림
    - universe 정렬해 순서 영향 제거
    """
    asof = node_input.get("asof")
    day = None
    if asof:
        day = str(asof)[:10]  # 'YYYY-MM-DD' 정도로 고정

    universe = sorted(node_input.get("universe", []))

    key_obj = {"day": day, "universe": universe}
    return json.dumps(key_obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def build_root_graph(llm_factory=get_openai_client):
    """root graph 빌더.

    AGENT_TIERS에 정의된 에이전트별 tier에 따라 필요한 LLM 클라이언트만 생성·재사용한다.
    (현재 배분은 3개 tier(BASE/LIGHT/HEAVY)를 사용 → 클라이언트 3개만 생성된다.)

    Args:
        llm_factory: tier를 받아 클라이언트를 반환하는 팩토리. 테스트에서 mock 주입용으로 교체 가능.
    """
    _clients: dict[LLMTier, object] = {}

    def client_for(node: str):
        tier = AGENT_TIERS[node]
        if tier not in _clients:
            _clients[tier] = llm_factory(tier)
        return _clients[tier]

    g = StateGraph(ParentState)

    crawler = build_crawler_graph(client_for("CRAWLER"))
    momo = build_momo_graph(client_for("MOMO"))
    fund = build_fund_graph(client_for("FUND"))
    reviewer = build_reviewer_graph(client_for("REVIEWER"))
    risk = build_risk_graph(client_for("RISK"))
    decider = build_decider_graph(client_for("DECIDER"))
    reporter = build_reporter_graph(client_for("REPORTER"))

    g.add_node(
        "CRAWLER",
        node_subgraph(crawler, adapt_parent_to_crawler_in, adapt_crawler_to_parent_out),
        cache_policy=CachePolicy(ttl=60 * 60 * 24, key_func=crawler_cache_key),
    )
    g.add_node("MOMO", node_subgraph(momo, adapt_parent_to_momo_in, adapt_momo_to_parent_out))
    g.add_node("FUND", node_subgraph(fund, adapt_parent_to_fund_in, adapt_fund_to_parent_out))
    g.add_node(
        "REVIEWER",
        node_subgraph(reviewer, adapt_parent_to_reviewer_in, adapt_reviewer_to_parent_out),
    )
    g.add_node("RISK", node_subgraph(risk, adapt_parent_to_risk_in, adapt_risk_to_parent_out))
    g.add_node(
        "DECIDER",
        node_subgraph(decider, adapt_parent_to_decider_in, adapt_decider_to_parent_out),
    )
    g.add_node(
        "REPORTER",
        node_subgraph(reporter, adapt_parent_to_reporter_in, adapt_reporter_to_parent_out),
    )

    # Pipeline flow according to agent-pipeline.md:
    # 1. START → (CRAWLER, REVIEWER) - parallel
    g.add_edge(START, "CRAWLER")
    g.add_edge(START, "REVIEWER")

    # 2. CRAWLER → (MOMO, FUND) - parallel
    g.add_edge("CRAWLER", "MOMO")
    g.add_edge("CRAWLER", "FUND")

    # 3. (MOMO, FUND, REVIEWER) → RISK - all feed into risk manager
    g.add_edge("MOMO", "RISK")
    g.add_edge("FUND", "RISK")
    g.add_edge("REVIEWER", "RISK")

    # 4. RISK → DECIDER → REPORTER → END
    g.add_edge("RISK", "DECIDER")
    g.add_edge("DECIDER", "REPORTER")
    g.add_edge("REPORTER", END)

    return g.compile(cache=InMemoryCache())
