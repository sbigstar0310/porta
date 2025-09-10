# graph/root_graph.py
from langgraph.graph import StateGraph, START, END
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


def node_subgraph(subgraph, inbound, outbound):
    """부모↔자식 어댑터 래퍼"""

    def _call(state: ParentState) -> dict:
        sub_in = inbound(state)
        sub_out = subgraph.invoke(sub_in)
        return outbound(sub_out)

    return _call


def build_root_graph(llm_client):
    """LLM 클라이언트를 주입받는 root graph 빌더"""
    g = StateGraph(ParentState)

    crawler = build_crawler_graph(llm_client)
    momo = build_momo_graph(llm_client)
    fund = build_fund_graph(llm_client)
    reviewer = build_reviewer_graph(llm_client)
    risk = build_risk_graph(llm_client)
    decider = build_decider_graph(llm_client)
    reporter = build_reporter_graph(llm_client)

    g.add_node(
        "CRAWLER",
        node_subgraph(crawler, adapt_parent_to_crawler_in, adapt_crawler_to_parent_out),
    )
    g.add_node(
        "MOMO", node_subgraph(momo, adapt_parent_to_momo_in, adapt_momo_to_parent_out)
    )
    g.add_node(
        "FUND", node_subgraph(fund, adapt_parent_to_fund_in, adapt_fund_to_parent_out)
    )
    g.add_node(
        "REVIEWER",
        node_subgraph(
            reviewer, adapt_parent_to_reviewer_in, adapt_reviewer_to_parent_out
        ),
    )
    g.add_node(
        "RISK", node_subgraph(risk, adapt_parent_to_risk_in, adapt_risk_to_parent_out)
    )
    g.add_node(
        "DECIDER",
        node_subgraph(decider, adapt_parent_to_decider_in, adapt_decider_to_parent_out),
    )
    g.add_node(
        "REPORTER",
        node_subgraph(
            reporter, adapt_parent_to_reporter_in, adapt_reporter_to_parent_out
        ),
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

    return g.compile()
