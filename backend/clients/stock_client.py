import yfinance as yf
import pandas as pd
import requests
import logging
from typing import Dict, List, Any
from data.schemas import StockSearchOut
from clients.cache_client import CacheClient

logger = logging.getLogger(__name__)


class StockClient:
    _cache_client = None

    def __init__(self): ...

    @classmethod
    def get_cache_client(cls) -> CacheClient:
        if cls._cache_client is None:
            cls._cache_client = CacheClient()
        return cls._cache_client

    @classmethod
    def search_stock(cls, query: str) -> List[StockSearchOut]:
        """
        종목 검색

        Args:
            query: 검색할 티커의 일부 또는 회사명의 일부

        Returns:
            List[StockSearchOut]: 후보 종목 목록 (ticker, company_name 포함)

        Examples:
            - search_stock("M") -> [StockSearchOut(ticker="MSFT", company_name="Microsoft Corporation"), ...]
            - search_stock("Micro") -> [StockSearchOut(ticker="MSFT", company_name="Microsoft Corporation")]
            - search_stock("AAPL") -> [StockSearchOut(ticker="AAPL", company_name="Apple Inc.")]
        """

        try:
            # Yahoo Finance 자동완성 API 사용 (비공식)
            url = "https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                "q": query,
                "lang": "en-US",
                "region": "US",
                "quotesCount": 10,
                "newsCount": 0,
                "enableFuzzyQuery": False,
                "quotesQueryId": "tss_match_phrase_query",
            }

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            quotes = data.get("quotes", [])

            # 티커와 회사명 추출 (주식만 필터링)
            stocks = []
            seen_tickers = set()  # 중복 방지

            for quote in quotes:
                if quote.get("quoteType") == "EQUITY" and quote.get("symbol"):
                    symbol = quote["symbol"]
                    # 불필요한 접미사 제거 (.L, .DE 등 해외 거래소 접미사)
                    if "." not in symbol or symbol.endswith(".US"):
                        clean_symbol = symbol.replace(".US", "")

                        # 중복 체크
                        if clean_symbol not in seen_tickers:
                            seen_tickers.add(clean_symbol)

                            # 회사명 추출 (shortname 우선, 없으면 longname)
                            company_name = quote.get("shortname") or quote.get("longname") or clean_symbol

                            stocks.append(StockSearchOut(ticker=clean_symbol, company_name=company_name))

            # 최대 10개만 반환
            return stocks[:10]

        except requests.exceptions.RequestException as e:
            logger.error(f"종목 검색 중 네트워크 오류: {e}")
            raise e
        except Exception as e:
            logger.error(f"종목 검색 중 오류: {e}")
            raise e

    @classmethod
    def _get_stock_data_with_cache(cls, ticker: str, period: str = "3mo") -> Dict[str, Any]:
        """개별 티커 캐싱"""
        cache_client = cls.get_cache_client()

        # 시간 버킷팅 적용
        cache_key = f"_get_stock_data_with_cache:{ticker}:{period}"

        def fetch_single_ticker():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                info = stock.info
                calendar = stock.calendar

                # 데이터 품질 검증
                if hist.empty:
                    logger.warning(f"No historical data for {ticker}")
                    return {
                        "status": "error",
                        "error": f"No historical data for {ticker}",
                        "stock_history": pd.DataFrame(),
                        "stock_info": {},
                        "stock_calendar": pd.DataFrame(),
                    }

                logger.debug(f"Successfully fetched {len(hist)} days of data for {ticker}")
                return {
                    "status": "success",
                    "stock_history": hist,
                    "stock_info": info,
                    "stock_calendar": calendar,
                }

            except Exception as e:
                logger.error(f"Failed to fetch data for {ticker}: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "stock_history": pd.DataFrame(),
                    "stock_info": {},
                    "stock_calendar": pd.DataFrame(),
                }

        # 24시간 캐시 (장기 데이터이므로 하루 차이는 미미함)
        return cache_client.get_or_set(cache_key, fetch_single_ticker, ttl_seconds=24 * 60 * 60)

    @classmethod
    def get_stock_data(cls, tickers: List[str], period: str = "3mo") -> Dict[str, Any]:
        """
        주식 데이터를 가져오는 도구

        Args:
            tickers: 주식 티커 리스트 (예: ["AAPL", "MSFT"])
            period: 데이터 기간 ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y",
                    "ytd", "max")

        Returns:
            Dict containing stock data for all tickers with cache info

        Example:
        ```json
            {
            "status": "success",
            "stock_history": {
                "AAPL": dict,
                "MSFT": dict,
            },
            "stock_info": {
                "AAPL": dict,
                "MSFT": dict,
            },
            "stock_calendar": {
                "AAPL": dict,
                "MSFT": dict,
            },
            }
        ```
        """
        try:
            stock_history = {}
            stock_info = {}
            stock_calendar = {}
            for ticker in tickers:
                # 개별 티커 일일 캐싱 사용
                ticker_data = cls._get_stock_data_with_cache(ticker, period)
                stock_history[ticker] = ticker_data["stock_history"]
                stock_info[ticker] = ticker_data["stock_info"]
                stock_calendar[ticker] = ticker_data["stock_calendar"]

            return {
                "status": "success",
                "stock_history": stock_history,
                "stock_info": stock_info,
                "stock_calendar": stock_calendar,
            }

        except Exception as e:
            logger.error(f"Critical error in get_stock_data: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    @classmethod
    def get_stock_current_price(cls, tickers: List[str]) -> Dict[str, float]:
        current_prices = {}
        for ticker in tickers:
            current_prices[ticker] = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
        return current_prices

    @classmethod
    def get_atr_pct(cls, ticker: str, period: str = "6mo", window: int = 14) -> float:
        """ATR% (변동성 비율) 계산"""
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return 0.0

        high_low = hist["High"] - hist["Low"]
        high_close = (hist["High"] - hist["Close"].shift()).abs()
        low_close = (hist["Low"] - hist["Close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        atr = tr.rolling(window=window).mean().iloc[-1]
        last_close = hist["Close"].iloc[-1]
        return float(atr / last_close)
