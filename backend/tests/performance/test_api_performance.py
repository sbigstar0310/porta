# tests/performance/test_api_performance.py
"""
API 성능 테스트
"""
import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import app
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.performance
class TestAPIPerformance:
    """API 성능 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def performance_timer(self):
        """성능 측정용 타이머"""

        class Timer:
            def __init__(self):
                self.start_time = None
                self.end_time = None

            def start(self):
                self.start_time = time.time()

            def stop(self):
                self.end_time = time.time()

            @property
            def elapsed(self):
                if self.start_time and self.end_time:
                    return self.end_time - self.start_time
                return None

        return Timer()

    def test_health_endpoint_performance(self, client, performance_timer):
        """헬스체크 엔드포인트 성능 테스트"""
        performance_timer.start()
        response = client.get("/health")
        performance_timer.stop()

        # 응답 시간이 100ms 이내여야 함
        assert performance_timer.elapsed < 0.1
        assert response.status_code == 200

    @patch("routers.health.Database")
    def test_health_db_endpoint_performance(self, mock_database, client, performance_timer):
        """DB 헬스체크 엔드포인트 성능 테스트"""
        # Mock Database health check
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.return_value = {
            "status": "healthy",
            "connected": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        mock_database.return_value = mock_db_instance

        performance_timer.start()
        response = client.get("/health/db")
        performance_timer.stop()

        # DB 헬스체크 응답 시간이 500ms 이내여야 함
        assert performance_timer.elapsed < 0.5
        assert response.status_code == 200

    @patch("routers.user.get_user_usecase")
    def test_user_api_performance(self, mock_get_usecase, client, performance_timer):
        """사용자 API 성능 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_user_profile.return_value = MockDataGenerator.create_user()
        mock_get_usecase.return_value = mock_usecase

        performance_timer.start()
        response = client.get("/users/1")
        performance_timer.stop()

        # 사용자 조회 응답 시간이 1초 이내여야 함
        assert performance_timer.elapsed < 1.0
        assert response.status_code == 200

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_portfolio_api_performance(self, mock_get_usecase, client, performance_timer):
        """포트폴리오 API 성능 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_portfolio.return_value = MockDataGenerator.create_portfolio()
        mock_get_usecase.return_value = mock_usecase

        performance_timer.start()
        response = client.get("/portfolios/1")
        performance_timer.stop()

        # 포트폴리오 조회 응답 시간이 1초 이내여야 함
        assert performance_timer.elapsed < 1.0
        assert response.status_code == 200

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_portfolio_list_performance(self, mock_get_usecase, client, performance_timer):
        """포트폴리오 목록 조회 성능 테스트"""
        # Mock usecase with large dataset
        mock_usecase = MagicMock()
        portfolios = MockDataGenerator.create_multiple_portfolios(50, user_id=1)
        mock_usecase.get_user_portfolios.return_value = portfolios
        mock_get_usecase.return_value = mock_usecase

        performance_timer.start()
        response = client.get("/portfolios/user/1")
        performance_timer.stop()

        # 50개 포트폴리오 목록 조회 시간이 2초 이내여야 함
        assert performance_timer.elapsed < 2.0
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 50

    def test_concurrent_requests_performance(self, client):
        """동시 요청 성능 테스트"""
        import concurrent.futures
        import threading

        def make_request():
            return client.get("/health")

        # 10개의 동시 요청
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # 10개 동시 요청이 5초 이내에 완료되어야 함
        assert total_time < 5.0

        # 모든 요청이 성공해야 함
        assert all(response.status_code == 200 for response in responses)

    def test_api_throughput(self, client):
        """API 처리량 테스트"""
        request_count = 100
        start_time = time.time()

        # 100개 순차 요청
        for _ in range(request_count):
            response = client.get("/health")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # 초당 요청 처리량 계산
        requests_per_second = request_count / total_time

        # 초당 최소 50개 요청을 처리할 수 있어야 함
        assert requests_per_second >= 50

    @patch("routers.user.get_user_usecase")
    def test_large_response_performance(self, mock_get_usecase, client, performance_timer):
        """큰 응답 데이터 성능 테스트"""
        # Mock usecase with large user data
        mock_usecase = MagicMock()

        # 큰 사용자 데이터 생성 (많은 필드가 있는 경우를 시뮬레이션)
        large_user_data = MockDataGenerator.create_user()
        large_user_data["extra_data"] = "x" * 10000  # 10KB 추가 데이터
        mock_usecase.get_user_profile.return_value = large_user_data
        mock_get_usecase.return_value = mock_usecase

        performance_timer.start()
        response = client.get("/users/1")
        performance_timer.stop()

        # 큰 응답도 2초 이내에 처리되어야 함
        assert performance_timer.elapsed < 2.0
        assert response.status_code == 200

    def test_api_memory_usage(self, client):
        """API 메모리 사용량 테스트"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # 시작 메모리 사용량
        initial_memory = process.memory_info().rss

        # 많은 요청 수행
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

        # 끝 메모리 사용량
        final_memory = process.memory_info().rss

        # 메모리 증가량이 100MB 이내여야 함
        memory_increase = final_memory - initial_memory
        assert memory_increase < 100 * 1024 * 1024  # 100MB

    def test_api_response_size(self, client):
        """API 응답 크기 테스트"""
        response = client.get("/health")

        assert response.status_code == 200

        # 응답 크기가 1KB 이내여야 함
        response_size = len(response.content)
        assert response_size < 1024

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_database_query_performance(self, mock_get_usecase, client, performance_timer):
        """데이터베이스 쿼리 성능 테스트"""
        # Mock slow database query
        mock_usecase = MagicMock()

        def slow_query(*args, **kwargs):
            time.sleep(0.1)  # 100ms 지연 시뮬레이션
            return MockDataGenerator.create_portfolio()

        mock_usecase.get_portfolio.side_effect = slow_query
        mock_get_usecase.return_value = mock_usecase

        performance_timer.start()
        response = client.get("/portfolios/1")
        performance_timer.stop()

        # 느린 쿼리가 있어도 전체 응답 시간이 1초 이내여야 함
        assert performance_timer.elapsed < 1.0
        assert response.status_code == 200

    def test_api_error_handling_performance(self, client, performance_timer):
        """API 오류 처리 성능 테스트"""
        performance_timer.start()
        response = client.get("/nonexistent-endpoint")
        performance_timer.stop()

        # 404 오류도 빠르게 처리되어야 함
        assert performance_timer.elapsed < 0.1
        assert response.status_code == 404
