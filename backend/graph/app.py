# app.py
from graph.root_graph import build_root_graph
import os
from schemas import ParentState
from datetime import datetime
from data.schemas import PortfolioOut
from llm_clients.openai_client import get_openai_client


def activate_langsmith():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "porta"


def run_graph(portfolio: PortfolioOut) -> dict:
    """
    Porta Agent Pipeline 실행

    Args:
        portfolio: PortfolioOut

    Returns:
        dict: 파이프라인 결과
    """
    # activate langsmith
    activate_langsmith()

    # llm client
    llm_client = get_openai_client()

    # build root graph
    app = build_root_graph(llm_client)

    # initial state
    initial_state: ParentState = ParentState(
        messages=[],
        portfolio=portfolio.model_dump(),
        universe=[pos.ticker for pos in portfolio.positions],
        asof=datetime.utcnow().isoformat(),
        language="ko",
    )

    # invoke pipeline
    out = app.invoke(initial_state)

    print("=== DECISIONS ===")
    for d in out.get("decisions", []):
        print(d)

    print("\n=== REPORT ===")
    print(out.get("report_md", ""))

    return out
