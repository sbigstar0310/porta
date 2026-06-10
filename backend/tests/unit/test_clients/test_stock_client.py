# tests/unit/test_clients/test_stock_client.py
"""
StockClient 단위 테스트
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from typing import List, Dict, Any

from clients.stock_client import StockClient


@pytest.mark.unit
class TestStockClient:
    """StockClient 테스트 클래스"""

    @pytest.fixture
    def stock_client(self):
        """StockClient 인스턴스"""
        return StockClient()

    @pytest.fixture
    def sample_tickers(self):
        """테스트용 티커 리스트"""
        return ["AAPL", "MSFT", "GOOGL"]

    @pytest.fixture
    def mock_stock_history_data(self):
        """Mock 주식 히스토리 데이터"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        return pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0, 153.0, 154.0],
                "High": [155.0, 156.0, 157.0, 158.0, 159.0],
                "Low": [148.0, 149.0, 150.0, 151.0, 152.0],
                "Close": [152.0, 153.0, 154.0, 155.0, 156.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            },
            index=dates,
        )

    @pytest.fixture
    def mock_stock_info_data(self):
        """Mock 주식 정보 데이터"""
        return {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "currentPrice": 156.0,
            "marketCap": 2400000000000,
            "trailingPE": 25.5,
            "forwardPE": 22.8,
            "dividendYield": 0.0045,
            "beta": 1.2,
        }

    def test_stock_client_initialization(self, stock_client):
        """StockClient 초기화 테스트"""
        assert isinstance(stock_client, StockClient)

    @patch("clients.stock_client.yf.download")
    @patch("clients.stock_client.yf.Ticker")
    def test_get_stock_data_success(
        self, mock_ticker, mock_download, stock_client, sample_tickers, mock_stock_history_data, mock_stock_info_data
    ):
        """주식 데이터 조회 성공 테스트"""
        # Mock yfinance download
        mock_download.return_value = mock_stock_history_data

        # Mock yfinance Ticker
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = mock_stock_info_data
        mock_ticker.return_value = mock_ticker_instance

        result = stock_client.get_stock_data(sample_tickers, period="1mo")

        # 호출 검증
        mock_download.assert_called_once_with(sample_tickers, period="1mo", group_by="ticker")

        # 결과 검증
        assert result["status"] == "success"
        assert "stock_history" in result
        assert "stock_info" in result
        assert len(result["stock_history"]) > 0

    @patch("clients.stock_client.yf.download")
    def test_get_stock_data_download_failure(self, mock_download, stock_client, sample_tickers):
        """주식 데이터 다운로드 실패 테스트"""
        mock_download.side_effect = Exception("Download failed")

        result = stock_client.get_stock_data(sample_tickers)

        # 결과 검증
        assert result["status"] == "error"
        assert "error" in result
        assert "Download failed" in result["error"]

    @patch("clients.stock_client.yf.download")
    def test_get_stock_data_empty_tickers(self, mock_download, stock_client):
        """빈 티커 리스트 테스트"""
        result = stock_client.get_stock_data([])

        # 빈 리스트는 download 호출하지 않음
        mock_download.assert_not_called()

        # 결과 검증
        assert result["status"] == "error"
        assert "No tickers provided" in result["error"]

    @patch("clients.stock_client.yf.download")
    def test_get_stock_data_invalid_period(self, mock_download, stock_client, sample_tickers):
        """잘못된 기간 설정 테스트"""
        mock_download.side_effect = ValueError("Invalid period")

        result = stock_client.get_stock_data(sample_tickers, period="invalid")

        # 결과 검증
        assert result["status"] == "error"
        assert "Invalid period" in result["error"]

    @patch("clients.stock_client.yf.Ticker")
    def test_get_single_stock_info_success(self, mock_ticker, stock_client, mock_stock_info_data):
        """단일 주식 정보 조회 성공 테스트"""
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = mock_stock_info_data
        mock_ticker.return_value = mock_ticker_instance

        result = stock_client.get_single_stock_info("AAPL")

        # 호출 검증
        mock_ticker.assert_called_once_with("AAPL")

        # 결과 검증
        assert result["status"] == "success"
        assert result["stock_info"]["symbol"] == "AAPL"
        assert result["stock_info"]["currentPrice"] == 156.0

    @patch("clients.stock_client.yf.Ticker")
    def test_get_single_stock_info_failure(self, mock_ticker, stock_client):
        """단일 주식 정보 조회 실패 테스트"""
        mock_ticker.side_effect = Exception("Ticker not found")

        result = stock_client.get_single_stock_info("INVALID")

        # 결과 검증
        assert result["status"] == "error"
        assert "Ticker not found" in result["error"]

    @patch("clients.stock_client.yf.download")
    def test_get_stock_history_only_success(self, mock_download, stock_client, sample_tickers, mock_stock_history_data):
        """주식 히스토리만 조회 성공 테스트"""
        mock_download.return_value = mock_stock_history_data

        result = stock_client.get_stock_history_only(sample_tickers, period="3mo")

        # 호출 검증
        mock_download.assert_called_once_with(sample_tickers, period="3mo", group_by="ticker")

        # 결과 검증
        assert result["status"] == "success"
        assert "stock_history" in result
        assert "stock_info" not in result  # 정보는 포함되지 않음

    def test_validate_tickers_valid(self, stock_client):
        """유효한 티커 검증 테스트"""
        valid_tickers = ["AAPL", "MSFT", "GOOGL", "BRK-B", "BRK.A"]

        for ticker in valid_tickers:
            assert stock_client.validate_ticker(ticker) is True

    def test_validate_tickers_invalid(self, stock_client):
        """유효하지 않은 티커 검증 테스트"""
        invalid_tickers = ["", "123", "invalid_ticker", "TOOLONGTICKERCODE"]

        for ticker in invalid_tickers:
            assert stock_client.validate_ticker(ticker) is False

    def test_format_stock_data_success(self, stock_client, mock_stock_history_data, mock_stock_info_data):
        """주식 데이터 포맷팅 성공 테스트"""
        raw_data = {"AAPL": mock_stock_history_data}

        info_data = {"AAPL": mock_stock_info_data}

        result = stock_client.format_stock_data(raw_data, info_data)

        # 결과 검증
        assert result["status"] == "success"
        assert "AAPL" in result["stock_history"]
        assert "AAPL" in result["stock_info"]
        assert len(result["stock_history"]["AAPL"]) == 5  # 5일치 데이터

    def test_calculate_technical_indicators_success(self, stock_client, mock_stock_history_data):
        """기술적 지표 계산 성공 테스트"""
        result = stock_client.calculate_technical_indicators(mock_stock_history_data)

        # 결과 검증
        assert "sma_20" in result
        assert "rsi" in result
        assert "bollinger_upper" in result
        assert "bollinger_lower" in result
        assert len(result["sma_20"]) <= len(mock_stock_history_data)

    @patch("clients.stock_client.yf.download")
    def test_get_stock_data_with_indicators(self, mock_download, stock_client, sample_tickers, mock_stock_history_data):
        """기술적 지표 포함 주식 데이터 조회 테스트"""
        mock_download.return_value = mock_stock_history_data

        result = stock_client.get_stock_data_with_indicators(sample_tickers, period="1mo")

        # 결과 검증
        assert result["status"] == "success"
        assert "technical_indicators" in result
        for ticker in sample_tickers:
            if ticker in result["technical_indicators"]:
                assert "sma_20" in result["technical_indicators"][ticker]
                assert "rsi" in result["technical_indicators"][ticker]

    def test_period_validation(self, stock_client):
        """기간 검증 테스트"""
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

        for period in valid_periods:
            assert stock_client.validate_period(period) is True

        invalid_periods = ["1w", "2mo", "invalid"]

        for period in invalid_periods:
            assert stock_client.validate_period(period) is False

    @patch("clients.stock_client.yf.download")
    def test_get_stock_data_performance_metrics(
        self, mock_download, stock_client, sample_tickers, mock_stock_history_data
    ):
        """성과 지표 포함 주식 데이터 조회 테스트"""
        mock_download.return_value = mock_stock_history_data

        result = stock_client.get_stock_data_with_performance(sample_tickers, period="1mo")

        # 결과 검증
        assert result["status"] == "success"
        assert "performance_metrics" in result
        for ticker in sample_tickers:
            if ticker in result["performance_metrics"]:
                metrics = result["performance_metrics"][ticker]
                assert "total_return" in metrics
                assert "volatility" in metrics
                assert "sharpe_ratio" in metrics

    def test_handle_network_errors(self, stock_client):
        """네트워크 오류 처리 테스트"""
        with patch("clients.stock_client.yf.download") as mock_download:
            mock_download.side_effect = ConnectionError("Network error")

            result = stock_client.get_stock_data(["AAPL"])

            assert result["status"] == "error"
            assert "Network error" in result["error"]

    def test_handle_timeout_errors(self, stock_client):
        """타임아웃 오류 처리 테스트"""
        with patch("clients.stock_client.yf.download") as mock_download:
            mock_download.side_effect = TimeoutError("Request timeout")

            result = stock_client.get_stock_data(["AAPL"])

            assert result["status"] == "error"
            assert "Request timeout" in result["error"]

    @patch("clients.stock_client.yf.download")
    def test_get_stock_data_large_dataset(self, mock_download, stock_client):
        """대용량 데이터셋 처리 테스트"""
        # 대용량 티커 리스트
        large_tickers = [f"STOCK{i}" for i in range(100)]

        # Mock 대용량 데이터
        large_data = pd.DataFrame(
            {
                "Open": [100.0] * 1000,
                "High": [105.0] * 1000,
                "Low": [95.0] * 1000,
                "Close": [102.0] * 1000,
                "Volume": [1000000] * 1000,
            }
        )

        mock_download.return_value = large_data

        result = stock_client.get_stock_data(large_tickers, period="1y")

        # 결과 검증
        assert result["status"] == "success"
        # 대용량 데이터 처리 확인
        assert len(result["stock_history"]) > 0

    def test_concurrent_requests_handling(self, stock_client):
        """동시 요청 처리 테스트"""
        # 이 테스트는 실제 동시성 처리가 구현된 경우에만 의미가 있음
        # 현재는 플레이스홀더로 두고, 향후 구현 시 확장
        pass

    def test_data_caching_mechanism(self, stock_client):
        """데이터 캐싱 메커니즘 테스트"""
        # 캐싱이 구현된 경우를 위한 플레이스홀더
        # 향후 캐싱 로직 구현 시 확장
        pass
