# tools/news.py
"""Finnhub 기반 뉴스 도구 (CRAWLER용). 키 미설정 시 status로 알리고 웹검색으로 강등."""
import logging
from typing import Any, Dict, List

from langchain_core.tools import tool
from clients import get_finnhub_client

logger = logging.getLogger(__name__)


@tool
def get_market_news() -> Dict[str, Any]:
    """미국 시장 전반의 최신 뉴스 헤드라인을 가져옵니다 (신규 종목 후보 발굴용).

    Returns:
        {"status": "success", "articles": [{headline, summary, url, source, published_at, related}]}
        키가 없거나 실패하면 {"status": "unavailable"|"error", ...} — 이 경우 web_search_tool을 사용하세요.
    """
    client = get_finnhub_client()
    if not client.is_available():
        return {"status": "unavailable", "error": "news feed not configured — use web search instead"}
    try:
        return {"status": "success", "articles": client.get_market_news()}
    except Exception as e:
        logger.error(f"Failed to fetch market news: {e}")
        return {"status": "error", "error": str(e)}


@tool
def get_company_news(tickers: List[str]) -> Dict[str, Any]:
    """특정 종목들의 최근 7일 뉴스를 가져옵니다 (후보 교차 검증용).

    Args:
        tickers: 조회할 티커 리스트 (최대 10개)

    Returns:
        {"status": "success", "news": {ticker: [{headline, summary, url, ...}]}}
    """
    client = get_finnhub_client()
    if not client.is_available():
        return {"status": "unavailable", "error": "news feed not configured — use web search instead"}
    try:
        news = {ticker: client.get_company_news(ticker, limit=5) for ticker in tickers[:10]}
        return {"status": "success", "news": news}
    except Exception as e:
        logger.error(f"Failed to fetch company news: {e}")
        return {"status": "error", "error": str(e)}
