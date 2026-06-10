# tests/unit/test_graph/test_tools/test_news_tools.py
"""뉴스 도구(graph/tools/news.py) 단위 테스트"""
import pytest
from unittest.mock import MagicMock, patch

from graph.tools.news import get_market_news, get_company_news


@pytest.mark.unit
class TestNewsTools:
    def test_market_news_unavailable_without_key(self):
        client = MagicMock()
        client.is_available.return_value = False
        with patch("graph.tools.news.get_finnhub_client", return_value=client):
            result = get_market_news.invoke({})
        assert result["status"] == "unavailable"
        assert "web search" in result["error"]

    def test_market_news_success(self):
        client = MagicMock()
        client.is_available.return_value = True
        client.get_market_news.return_value = [{"headline": "h", "related": "AAPL"}]
        with patch("graph.tools.news.get_finnhub_client", return_value=client):
            result = get_market_news.invoke({})
        assert result["status"] == "success"
        assert result["articles"][0]["headline"] == "h"

    def test_market_news_error_path(self):
        client = MagicMock()
        client.is_available.return_value = True
        client.get_market_news.side_effect = RuntimeError("boom")
        with patch("graph.tools.news.get_finnhub_client", return_value=client):
            result = get_market_news.invoke({})
        assert result["status"] == "error"

    def test_company_news_caps_ticker_count(self):
        client = MagicMock()
        client.is_available.return_value = True
        client.get_company_news.return_value = []
        with patch("graph.tools.news.get_finnhub_client", return_value=client):
            result = get_company_news.invoke({"tickers": [f"T{i}" for i in range(15)]})
        assert result["status"] == "success"
        assert client.get_company_news.call_count == 10  # 최대 10개 티커
