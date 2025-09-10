# app.py
from graph.root_graph import build_root_graph
import os


def activate_langsmith():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "porta"


def run_graph(sample_input: dict | None = None):
    # activate langsmith
    activate_langsmith()

    app = build_root_graph()
    # 샘플 입력
    init = sample_input or {
        "portfolio": {"cash": 10000, "positions": {"AAPL": 1.2}},
        "universe": ["AAPL", "NVDA", "TSLA"],
        "asof": "2025-09-06T08:00:00Z",
        "messages": [],
        # CRAWLER가 만든 값을 미리 넣어도 되고, 없으면 crawler가 생성
        # "crawl_prices": {"AAPL": {...}, ...}
    }
    out = app.invoke(init)
    print("=== DECISIONS ===")
    for d in out.get("decisions", []):
        print(d)
    print("\n=== REPORT ===")
    print(out.get("report_md", ""))
