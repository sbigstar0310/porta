import yfinance as yf
import pandas as pd
from typing import Dict, List, Any


class StockClient:
    def __init__(self): ...

    @classmethod
    def get_stock_data(cls, tickers: List[str], period: str = "3mo") -> Dict[str, Any]:
        """
        주식 데이터를 가져오는 도구

        Args:
            tickers: 주식 티커 리스트 (예: ["AAPL", "MSFT"])
            period: 데이터 기간 ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y",
                    "ytd", "max")

        Returns:
            Dict containing stock data for all tickers

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
                stock = yf.Ticker(ticker)
                stock_history[ticker] = stock.history(period=period)
                stock_info[ticker] = stock.info
                stock_calendar[ticker] = stock.calendar
            return {
                "status": "success",
                "stock_history": stock_history,
                "stock_info": stock_info,
                "stock_calendar": stock_calendar,
            }
        except Exception as e:
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
