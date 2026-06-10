# tests/unit/test_clients/test_finnhub_client.py
"""FinnhubClient 단위 테스트 (네트워크/캐시 없이)"""
import pytest
from unittest.mock import patch

from clients.finnhub_client import FinnhubClient


def make_client(api_key="test-key") -> FinnhubClient:
    with patch.object(FinnhubClient, "_init_cache", return_value=None):
        return FinnhubClient(api_key=api_key)


@pytest.mark.unit
class TestFinnhubClient:
    def test_unavailable_without_key(self):
        client = make_client(api_key="")
        assert client.is_available() is False
        with pytest.raises(RuntimeError):
            client._get("/quote", {"symbol": "AAPL"})

    def test_normalize_article(self):
        article = {
            "headline": "H" * 300,
            "summary": "S" * 500,
            "url": "https://example.com",
            "source": "Reuters",
            "datetime": 1750000000,
            "related": "AAPL,MSFT",
        }
        normalized = FinnhubClient._normalize_article(article)
        assert len(normalized["headline"]) == 200
        assert len(normalized["summary"]) == 400
        assert normalized["published_at"].startswith("2025-")
        assert normalized["related"] == "AAPL,MSFT"

    def test_get_upcoming_earnings_filters_and_picks_nearest(self):
        client = make_client()
        calendar = {
            "earningsCalendar": [
                {"symbol": "AAPL", "date": "2026-06-15"},
                {"symbol": "AAPL", "date": "2026-06-12"},  # 더 가까운 날짜 우선
                {"symbol": "MSFT", "date": "2026-06-13"},
                {"symbol": "OTHER", "date": "2026-06-14"},  # 요청 안 한 티커 제외
            ]
        }
        with patch.object(client, "_get", return_value=calendar):
            upcoming = client.get_upcoming_earnings(["aapl", "MSFT", "NVDA"], days=7)
        assert upcoming == {"AAPL": "2026-06-12", "MSFT": "2026-06-13"}

    def test_get_quote_invalid_price_returns_none(self):
        client = make_client()
        with patch.object(client, "_get", return_value={"c": 0}):
            assert client.get_quote("AAPL") is None
        with patch.object(client, "_get", return_value={"c": 123.45}):
            assert client.get_quote("AAPL") == 123.45

    def test_get_market_news_normalizes_and_limits(self):
        client = make_client()
        raw = [{"headline": f"news {i}", "datetime": 1750000000} for i in range(50)]
        with patch.object(client, "_get", return_value=raw):
            articles = client.get_market_news(limit=30)
        assert len(articles) == 30
        assert articles[0]["headline"] == "news 0"
