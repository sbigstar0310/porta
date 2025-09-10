from typing import List, Dict, Any
from duckduckgo_search import DDGS
from langchain_core.tools import tool


def search_web_with_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """DuckDuckGo 웹 검색 (뉴스/웹 혼합) 결과를 반환

    Returns: List of {title, url, snippet}
    """
    results: List[Dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": (item.get("title") or "")[:160],
                        "url": (item.get("href") or item.get("url") or ""),
                        "snippet": (item.get("body") or item.get("description") or "")[:400],
                    }
                )
    except Exception:
        # 실패 시 빈 리스트 반환 (상위 레이어에서 graceful degrade)
        return []
    return results


@tool
def web_search_tool(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """DuckDuckGo로 웹 검색을 수행하여 상위 결과를 반환합니다.

    Args:
        query: 검색 질의어
        max_results: 최대 결과 수 (기본 10)

    Returns:
        [{"title": str, "url": str, "snippet": str}, ...]
    """
    return search_web_with_duckduckgo(query=query, max_results=max_results)
