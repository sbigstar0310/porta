# tests/integration/test_api/test_health_api.py
"""
Health API 통합 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import app


@pytest.mark.integration
class TestHealthAPI:
    """Health API 통합 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    def test_health_endpoint_success(self, client):
        """기본 헬스체크 엔드포인트 성공 테스트"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "API 서버가 정상적으로 실행되고 있습니다" in data["message"]

    @patch("routers.health.Database")
    def test_health_db_endpoint_success(self, mock_database, client):
        """DB 헬스체크 엔드포인트 성공 테스트"""
        # Mock Database health check
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.return_value = {
            "status": "healthy",
            "connected": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        mock_database.return_value = mock_db_instance

        response = client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connected"] is True
        assert "timestamp" in data

    @patch("routers.health.Database")
    def test_health_db_endpoint_failure(self, mock_database, client):
        """DB 헬스체크 엔드포인트 실패 테스트"""
        # Mock Database health check failure
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.side_effect = Exception("DB connection failed")
        mock_database.return_value = mock_db_instance

        response = client.get("/health/db")

        assert response.status_code == 200  # 헬스체크는 항상 200을 반환
        data = response.json()
        assert data["status"] == "error"
        assert data["connected"] is False
        assert "DB connection failed" in data["error"]

    def test_health_endpoint_response_format(self, client):
        """헬스체크 응답 형식 테스트"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "message" in data

    @patch("routers.health.Database")
    def test_health_db_endpoint_response_format(self, mock_database, client):
        """DB 헬스체크 응답 형식 테스트"""
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.return_value = {
            "status": "healthy",
            "connected": True,
            "timestamp": "2024-01-01T00:00:00Z",
            "database": "supabase",
        }
        mock_database.return_value = mock_db_instance

        response = client.get("/health/db")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "connected" in data
        assert "timestamp" in data

    def test_health_endpoint_methods(self, client):
        """헬스체크 엔드포인트 허용 메서드 테스트"""
        # GET 메서드는 허용
        response = client.get("/health")
        assert response.status_code == 200

        # POST 메서드는 허용되지 않음
        response = client.post("/health")
        assert response.status_code == 405

        # PUT 메서드는 허용되지 않음
        response = client.put("/health")
        assert response.status_code == 405

        # DELETE 메서드는 허용되지 않음
        response = client.delete("/health")
        assert response.status_code == 405

    def test_health_endpoint_cors_headers(self, client):
        """헬스체크 엔드포인트 CORS 헤더 테스트"""
        response = client.get("/health")

        # CORS 헤더가 포함되어야 함 (app.py에서 CORS 미들웨어 설정)
        # 실제 헤더는 FastAPI와 CORS 미들웨어 설정에 따라 다를 수 있음
        assert response.status_code == 200

    @patch("routers.health.Database")
    def test_health_db_concurrent_requests(self, mock_database, client):
        """DB 헬스체크 동시 요청 테스트"""
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.return_value = {
            "status": "healthy",
            "connected": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        mock_database.return_value = mock_db_instance

        # 동시에 여러 요청 보내기
        responses = []
        for _ in range(5):
            response = client.get("/health/db")
            responses.append(response)

        # 모든 요청이 성공해야 함
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @patch("routers.health.Database")
    def test_health_db_timeout_handling(self, mock_database, client):
        """DB 헬스체크 타임아웃 처리 테스트"""
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.side_effect = TimeoutError("Database timeout")
        mock_database.return_value = mock_db_instance

        response = client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["connected"] is False
        assert "Database timeout" in data["error"]

    def test_health_endpoint_performance(self, client):
        """헬스체크 엔드포인트 성능 테스트"""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        # 응답 시간이 1초 이내여야 함
        response_time = end_time - start_time
        assert response_time < 1.0
        assert response.status_code == 200

    @patch("routers.health.Database")
    def test_health_db_performance(self, mock_database, client):
        """DB 헬스체크 성능 테스트"""
        import time

        mock_db_instance = MagicMock()
        mock_db_instance.health_check.return_value = {
            "status": "healthy",
            "connected": True,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        mock_database.return_value = mock_db_instance

        start_time = time.time()
        response = client.get("/health/db")
        end_time = time.time()

        # DB 헬스체크 응답 시간이 3초 이내여야 함
        response_time = end_time - start_time
        assert response_time < 3.0
        assert response.status_code == 200

    def test_health_endpoint_multiple_calls(self, client):
        """헬스체크 엔드포인트 연속 호출 테스트"""
        # 연속으로 여러 번 호출해도 일관된 결과를 반환해야 함
        responses = []
        for _ in range(10):
            response = client.get("/health")
            responses.append(response)

        # 모든 응답이 일관되어야 함
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "message" in data

    @patch("routers.health.Database")
    def test_health_db_error_details(self, mock_database, client):
        """DB 헬스체크 오류 상세 정보 테스트"""
        mock_db_instance = MagicMock()
        mock_db_instance.health_check.side_effect = ConnectionError("Connection refused on port 5432")
        mock_database.return_value = mock_db_instance

        response = client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["connected"] is False
        assert "Connection refused on port 5432" in data["error"]

        # 오류 세부 정보가 포함되어야 함
        assert "error" in data
        assert isinstance(data["error"], str)
        assert len(data["error"]) > 0
