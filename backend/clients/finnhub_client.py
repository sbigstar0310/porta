# clients/finnhub_client.py
"""Finnhub REST API 래퍼 (뉴스, 어닝스 캘린더, 시세 폴백).

- FINNHUB_API_KEY 미설정 시 is_available()가 False — 호출부는 기존 경로로 자동 강등.
- 무료 티어: 60콜/분. 캐싱(Redis)으로 호출 수를 더 줄인다.
- 라이선스 주의: 무료 티어는 개인용(personal use). 서비스 과금 시작 전에
  상용 라이선스 협의 필요 (https://finnhub.io/pricing-startups-and-enterprise).
"""
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://finnhub.io/api/v1"
REQUEST_TIMEOUT_SECONDS = 10

NEWS_CACHE_TTL = 3 * 60 * 60  # 뉴스 3시간 (일 1회 파이프라인 기준 충분)
EARNINGS_CACHE_TTL = 24 * 60 * 60  # 어닝스 캘린더 24시간


class FinnhubClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY", "")
        self.cache = self._init_cache()

    @staticmethod
    def _init_cache():
        # Redis가 없는 환경(로컬 테스트 등)에서도 클라이언트는 동작해야 한다
        try:
            from clients.cache_client import CacheClient

            return CacheClient()
        except Exception as e:
            logger.warning(f"Cache unavailable for FinnhubClient (continuing without cache): {e}")
            return None

    def is_available(self) -> bool:
        return bool(self.api_key)

    # ---- 공개 API ----

    def get_market_news(self, category: str = "general", limit: int = 30) -> List[Dict[str, Any]]:
        """시장 전반 뉴스 (CRAWLER의 후보 발굴용)."""
        def fetch():
            raw = self._get("/news", {"category": category})
            return [self._normalize_article(a) for a in raw[:limit]]

        return self._cached(f"finnhub:market_news:{category}", fetch, NEWS_CACHE_TTL)

    def get_company_news(self, symbol: str, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """특정 종목 뉴스 (최근 N일)."""
        to_date = datetime.now(timezone.utc).date()
        from_date = to_date - timedelta(days=days)

        def fetch():
            raw = self._get(
                "/company-news",
                {"symbol": symbol, "from": from_date.isoformat(), "to": to_date.isoformat()},
            )
            return [self._normalize_article(a) for a in raw[:limit]]

        return self._cached(f"finnhub:company_news:{symbol}:{to_date.isoformat()}", fetch, NEWS_CACHE_TTL)

    def get_upcoming_earnings(self, tickers: List[str], days: int = 7) -> Dict[str, str]:
        """티커별 가장 가까운 실적 발표일(YYYY-MM-DD). 향후 days일 내에 없는 티커는 제외."""
        from_date = datetime.now(timezone.utc).date()
        to_date = from_date + timedelta(days=days)

        def fetch():
            raw = self._get("/calendar/earnings", {"from": from_date.isoformat(), "to": to_date.isoformat()})
            return raw.get("earningsCalendar", [])

        calendar = self._cached(f"finnhub:earnings:{from_date.isoformat()}:{to_date.isoformat()}", fetch, EARNINGS_CACHE_TTL)

        wanted = {t.upper() for t in tickers}
        upcoming: Dict[str, str] = {}
        for entry in calendar:
            symbol = str(entry.get("symbol", "")).upper()
            event_date = entry.get("date")
            if symbol in wanted and event_date:
                if symbol not in upcoming or event_date < upcoming[symbol]:
                    upcoming[symbol] = event_date
        return upcoming

    def get_quote(self, symbol: str) -> Optional[float]:
        """현재가 (yfinance 실패 시 폴백용). 유효하지 않으면 None."""
        raw = self._get("/quote", {"symbol": symbol})
        price = raw.get("c")
        return float(price) if price and price > 0 else None

    # ---- 내부 헬퍼 ----

    def _get(self, path: str, params: Dict[str, Any]) -> Any:
        if not self.is_available():
            raise RuntimeError("FINNHUB_API_KEY is not configured")
        response = requests.get(
            f"{BASE_URL}{path}",
            params={**params, "token": self.api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def _cached(self, key: str, fetch: Callable[[], Any], ttl_seconds: int) -> Any:
        if self.cache is None:
            return fetch()
        return self.cache.get_or_set(key, fetch, ttl_seconds=ttl_seconds)

    @staticmethod
    def _normalize_article(article: Dict[str, Any]) -> Dict[str, Any]:
        published = article.get("datetime")
        if isinstance(published, (int, float)) and published > 0:
            published = datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
        return {
            "headline": str(article.get("headline", ""))[:200],
            "summary": str(article.get("summary", ""))[:400],
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "published_at": published,
            "related": article.get("related", ""),  # 관련 티커 (쉼표 구분)
        }
