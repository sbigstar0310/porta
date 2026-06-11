# tests/unit/test_clients/test_stock_client.py
"""
StockClient 단위 테스트 (네트워크/Redis 없이)

- 캐시(CacheClient.get_or_set)는 fetch 함수를 그대로 실행하도록 mock 처리
- yfinance(yf.Ticker), requests는 모두 mock 처리
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import requests

from clients.stock_client import StockClient


def make_passthrough_cache() -> MagicMock:
    """get_or_set이 캐시 없이 fetch 함수를 바로 실행하는 mock 캐시"""
    cache = MagicMock()
    cache.get_or_set.side_effect = lambda key, fetch, ttl_seconds=None: fetch()
    return cache


@pytest.fixture(autouse=True)
def reset_cache_singleton():
    """클래스 레벨 캐시 싱글톤 격리 (테스트 간 오염 방지)"""
    StockClient._cache_client = None
    yield
    StockClient._cache_client = None


@pytest.fixture
def mock_history() -> pd.DataFrame:
    """Mock 주가 히스토리 데이터 (5일치)"""
    dates = pd.date_range("2026-06-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "Open": [150.0, 151.0, 152.0, 153.0, 154.0],
            "High": [155.0, 156.0, 157.0, 158.0, 159.0],
            "Low": [148.0, 149.0, 150.0, 151.0, 152.0],
            "Close": [152.0, 153.0, 154.0, 155.0, 156.0],
            "Volume": [1_000_000, 1_100_000, 1_200_000, 1_300_000, 1_400_000],
        },
        index=dates,
    )


@pytest.fixture
def mock_info() -> dict:
    """Mock 종목 정보 데이터"""
    return {
        "symbol": "AAPL",
        "shortName": "Apple Inc.",
        "currentPrice": 156.0,
        "marketCap": 2_400_000_000_000,
    }


def make_mock_ticker(history: pd.DataFrame, info: dict, calendar=None) -> MagicMock:
    """yf.Ticker 인스턴스 mock 생성"""
    ticker = MagicMock()
    ticker.history.return_value = history
    ticker.info = info
    ticker.calendar = calendar if calendar is not None else pd.DataFrame()
    return ticker


@pytest.mark.unit
class TestGetStockData:
    """get_stock_data / _get_stock_data_with_cache 테스트"""

    @patch("clients.stock_client.yf.Ticker")
    def test_get_stock_data_success_aggregates_per_ticker(self, mock_ticker_cls, mock_history, mock_info):
        """티커별 history/info/calendar가 집계되어 반환되는지 테스트"""
        tickers = ["AAPL", "MSFT"]
        calendar = pd.DataFrame({"Earnings Date": [pd.Timestamp("2026-07-30")]})
        mock_ticker_cls.return_value = make_mock_ticker(mock_history, mock_info, calendar)

        with patch.object(StockClient, "get_cache_client", return_value=make_passthrough_cache()):
            result = StockClient.get_stock_data(tickers, period="1mo")

        assert result["status"] == "success"
        for ticker in tickers:
            assert ticker in result["stock_history"]
            assert ticker in result["stock_info"]
            assert ticker in result["stock_calendar"]
            pd.testing.assert_frame_equal(result["stock_history"][ticker], mock_history)
            assert result["stock_info"][ticker] == mock_info

        # 티커별로 yf.Ticker가 호출되고 period가 전달되는지 확인
        assert mock_ticker_cls.call_count == 2
        mock_ticker_cls.assert_any_call("AAPL")
        mock_ticker_cls.assert_any_call("MSFT")
        mock_ticker_cls.return_value.history.assert_called_with(period="1mo")

    @patch("clients.stock_client.yf.Ticker")
    def test_get_stock_data_uses_24h_cache_per_ticker(self, mock_ticker_cls, mock_history, mock_info):
        """티커별 캐시 키와 24시간 TTL로 get_or_set이 호출되는지 테스트"""
        mock_ticker_cls.return_value = make_mock_ticker(mock_history, mock_info)
        cache = make_passthrough_cache()

        with patch.object(StockClient, "get_cache_client", return_value=cache):
            StockClient.get_stock_data(["AAPL"], period="3mo")

        assert cache.get_or_set.call_count == 1
        call = cache.get_or_set.call_args
        assert call.args[0] == "_get_stock_data_with_cache:AAPL:3mo"
        assert call.kwargs["ttl_seconds"] == 24 * 60 * 60

    @patch("clients.stock_client.yf.Ticker")
    def test_get_stock_data_cache_hit_skips_yfinance(self, mock_ticker_cls, mock_history, mock_info):
        """캐시 히트 시 yfinance를 호출하지 않는지 테스트"""
        cached = {
            "status": "success",
            "stock_history": mock_history,
            "stock_info": mock_info,
            "stock_calendar": pd.DataFrame(),
        }
        cache = MagicMock()
        cache.get_or_set.return_value = cached  # fetch를 실행하지 않음 (캐시 히트)

        with patch.object(StockClient, "get_cache_client", return_value=cache):
            result = StockClient.get_stock_data(["AAPL"])

        mock_ticker_cls.assert_not_called()
        assert result["status"] == "success"
        assert result["stock_info"]["AAPL"] == mock_info

    @patch("clients.stock_client.yf.Ticker")
    def test_get_stock_data_empty_history_returns_error_entry(self, mock_ticker_cls, mock_info):
        """히스토리가 비어 있으면 해당 티커는 에러 엔트리(빈 데이터)로 처리되는지 테스트"""
        mock_ticker_cls.return_value = make_mock_ticker(pd.DataFrame(), mock_info)

        with patch.object(StockClient, "get_cache_client", return_value=make_passthrough_cache()):
            result = StockClient.get_stock_data(["DELISTED"])

        # 집계 자체는 성공이지만, 해당 티커 데이터는 비어 있어야 함
        assert result["status"] == "success"
        assert result["stock_history"]["DELISTED"].empty
        assert result["stock_info"]["DELISTED"] == {}
        assert result["stock_calendar"]["DELISTED"].empty

    @patch("clients.stock_client.yf.Ticker")
    def test_get_stock_data_fetch_exception_returns_error_entry(self, mock_ticker_cls):
        """yfinance 조회 중 예외 발생 시 해당 티커는 빈 데이터로 처리되는지 테스트"""
        mock_ticker_cls.side_effect = Exception("Network error")

        with patch.object(StockClient, "get_cache_client", return_value=make_passthrough_cache()):
            result = StockClient.get_stock_data(["AAPL"])

        assert result["status"] == "success"
        assert result["stock_history"]["AAPL"].empty
        assert result["stock_info"]["AAPL"] == {}

    def test_get_stock_data_cache_failure_returns_error(self):
        """캐시 계층 자체가 실패하면 전체 결과가 error인지 테스트"""
        cache = MagicMock()
        cache.get_or_set.side_effect = Exception("Redis connection failed")

        with patch.object(StockClient, "get_cache_client", return_value=cache):
            result = StockClient.get_stock_data(["AAPL"])

        assert result["status"] == "error"
        assert "Redis connection failed" in result["error"]

    def test_get_stock_data_empty_tickers_returns_empty_success(self):
        """빈 티커 리스트는 빈 집계 결과(success)를 반환하는지 테스트"""
        cache = make_passthrough_cache()
        with patch.object(StockClient, "get_cache_client", return_value=cache):
            result = StockClient.get_stock_data([])

        assert result["status"] == "success"
        assert result["stock_history"] == {}
        assert result["stock_info"] == {}
        assert result["stock_calendar"] == {}
        cache.get_or_set.assert_not_called()


@pytest.mark.unit
class TestGetStockCurrentPrice:
    """get_stock_current_price 테스트 (yfinance → Finnhub 폴백)"""

    @patch("clients.stock_client.yf.Ticker")
    def test_yfinance_success(self, mock_ticker_cls, mock_history):
        """yfinance로 현재가 조회 성공 테스트"""
        mock_ticker_cls.return_value = make_mock_ticker(mock_history, {})

        prices = StockClient.get_stock_current_price(["AAPL"])

        assert prices == {"AAPL": 156.0}  # 마지막 Close 값
        mock_ticker_cls.return_value.history.assert_called_with(period="1d")

    @patch("clients.finnhub_client.FinnhubClient")
    @patch("clients.stock_client.yf.Ticker")
    def test_yfinance_failure_falls_back_to_finnhub(self, mock_ticker_cls, mock_finnhub_cls):
        """yfinance 실패 시 Finnhub 폴백으로 가격을 가져오는지 테스트"""
        mock_ticker_cls.return_value.history.side_effect = Exception("yfinance down")
        mock_finnhub = mock_finnhub_cls.return_value
        mock_finnhub.is_available.return_value = True
        mock_finnhub.get_quote.return_value = 123.45

        prices = StockClient.get_stock_current_price(["AAPL"])

        assert prices == {"AAPL": 123.45}
        mock_finnhub.get_quote.assert_called_once_with("AAPL")

    @patch("clients.finnhub_client.FinnhubClient")
    @patch("clients.stock_client.yf.Ticker")
    def test_finnhub_unavailable_ticker_omitted(self, mock_ticker_cls, mock_finnhub_cls):
        """yfinance 실패 + Finnhub 키 미설정 시 티커가 결과에서 제외되는지 테스트"""
        mock_ticker_cls.return_value.history.side_effect = Exception("yfinance down")
        mock_finnhub = mock_finnhub_cls.return_value
        mock_finnhub.is_available.return_value = False

        prices = StockClient.get_stock_current_price(["AAPL"])

        assert prices == {}
        mock_finnhub.get_quote.assert_not_called()

    @patch("clients.finnhub_client.FinnhubClient")
    @patch("clients.stock_client.yf.Ticker")
    def test_both_sources_fail_ticker_omitted(self, mock_ticker_cls, mock_finnhub_cls):
        """yfinance와 Finnhub 모두 실패 시 티커가 결과에서 제외되는지 테스트"""
        mock_ticker_cls.return_value.history.side_effect = Exception("yfinance down")
        mock_finnhub = mock_finnhub_cls.return_value
        mock_finnhub.is_available.return_value = True
        mock_finnhub.get_quote.side_effect = Exception("Finnhub down")

        prices = StockClient.get_stock_current_price(["AAPL"])

        assert prices == {}

    @patch("clients.finnhub_client.FinnhubClient")
    @patch("clients.stock_client.yf.Ticker")
    def test_partial_success_mixed_sources(self, mock_ticker_cls, mock_finnhub_cls, mock_history):
        """일부는 yfinance, 일부는 Finnhub 폴백으로 가져오는 혼합 케이스 테스트"""
        ok_ticker = make_mock_ticker(mock_history, {})
        bad_ticker = MagicMock()
        bad_ticker.history.side_effect = Exception("no data")
        mock_ticker_cls.side_effect = lambda t: ok_ticker if t == "AAPL" else bad_ticker

        mock_finnhub = mock_finnhub_cls.return_value
        mock_finnhub.is_available.return_value = True
        mock_finnhub.get_quote.return_value = 99.9

        prices = StockClient.get_stock_current_price(["AAPL", "MSFT"])

        assert prices == {"AAPL": 156.0, "MSFT": 99.9}


@pytest.mark.unit
class TestSearchStock:
    """search_stock 테스트 (Yahoo 자동완성 API mock)"""

    @staticmethod
    def make_response(quotes: list) -> MagicMock:
        response = MagicMock()
        response.json.return_value = {"quotes": quotes}
        response.raise_for_status.return_value = None
        return response

    @patch("clients.stock_client.requests.get")
    def test_search_returns_equity_results(self, mock_get):
        """EQUITY 종목만 ticker/company_name으로 반환하는지 테스트"""
        quotes = [
            {"quoteType": "EQUITY", "symbol": "MSFT", "shortname": "Microsoft Corporation"},
            {"quoteType": "ETF", "symbol": "QQQ", "shortname": "Invesco QQQ"},  # 주식 아님 → 제외
            {"quoteType": "EQUITY", "symbol": "MSFT.DE", "shortname": "Microsoft (XETRA)"},  # 해외 접미사 → 제외
            {"quoteType": "EQUITY", "symbol": "AAPL.US", "longname": "Apple Inc."},  # .US 접미사 제거
        ]
        mock_get.return_value = self.make_response(quotes)

        results = StockClient.search_stock("M")

        assert [(r.ticker, r.company_name) for r in results] == [
            ("MSFT", "Microsoft Corporation"),
            ("AAPL", "Apple Inc."),
        ]

    @patch("clients.stock_client.requests.get")
    def test_search_limits_to_10_and_dedupes(self, mock_get):
        """결과가 최대 10개로 제한되고 중복 티커가 제거되는지 테스트"""
        quotes = [{"quoteType": "EQUITY", "symbol": f"TK{i}", "shortname": f"Company {i}"} for i in range(15)]
        quotes.append({"quoteType": "EQUITY", "symbol": "TK0", "shortname": "Duplicate"})  # 중복
        mock_get.return_value = self.make_response(quotes)

        results = StockClient.search_stock("TK")

        assert len(results) == 10
        tickers = [r.ticker for r in results]
        assert len(tickers) == len(set(tickers))

    @patch("clients.stock_client.requests.get")
    def test_search_company_name_fallback_to_symbol(self, mock_get):
        """shortname/longname이 모두 없으면 티커를 회사명으로 사용하는지 테스트"""
        mock_get.return_value = self.make_response([{"quoteType": "EQUITY", "symbol": "XYZ"}])

        results = StockClient.search_stock("XYZ")

        assert len(results) == 1
        assert results[0].company_name == "XYZ"

    @patch("clients.stock_client.requests.get")
    def test_search_empty_results(self, mock_get):
        """검색 결과가 없으면 빈 리스트를 반환하는지 테스트"""
        mock_get.return_value = self.make_response([])

        assert StockClient.search_stock("zzz-no-match") == []

    @patch("clients.stock_client.requests.get")
    def test_search_network_error_raises(self, mock_get):
        """네트워크 오류 시 예외가 전파되는지 테스트"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

        with pytest.raises(requests.exceptions.ConnectionError):
            StockClient.search_stock("AAPL")


@pytest.mark.unit
class TestGetAtrPct:
    """get_atr_pct 테스트"""

    @patch("clients.stock_client.yf.Ticker")
    def test_empty_history_returns_zero(self, mock_ticker_cls):
        """히스토리가 비어 있으면 0.0을 반환하는지 테스트"""
        mock_ticker_cls.return_value = make_mock_ticker(pd.DataFrame(), {})

        assert StockClient.get_atr_pct("DELISTED") == 0.0

    @patch("clients.stock_client.yf.Ticker")
    def test_atr_pct_computed_from_history(self, mock_ticker_cls):
        """충분한 데이터로 ATR% 가 양수 float로 계산되는지 테스트"""
        n = 30
        dates = pd.date_range("2026-01-01", periods=n, freq="D")
        hist = pd.DataFrame(
            {
                "Open": [100.0] * n,
                "High": [105.0] * n,
                "Low": [95.0] * n,
                "Close": [100.0] * n,
                "Volume": [1_000_000] * n,
            },
            index=dates,
        )
        mock_ticker_cls.return_value = make_mock_ticker(hist, {})

        atr_pct = StockClient.get_atr_pct("AAPL", window=14)

        # TR = High - Low = 10, Close = 100 → ATR% = 0.1
        assert isinstance(atr_pct, float)
        assert atr_pct == pytest.approx(0.1)
