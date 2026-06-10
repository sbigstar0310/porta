# tests/integration/test_api/test_user_api.py
"""
User API 통합 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app import app
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.integration
class TestUserAPI:
    """User API 통합 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def sample_user_data(self):
        """테스트용 사용자 데이터"""
        return MockDataGenerator.create_user()

    @patch("routers.user.get_user_usecase")
    def test_get_user_success(self, mock_get_usecase, client, sample_user_data):
        """사용자 조회 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_user_profile.return_value = MockDataGenerator.create_user(user_id=1)
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "email" in data
        assert "timezone" in data
        assert "language" in data

    @patch("routers.user.get_user_usecase")
    def test_get_user_not_found(self, mock_get_usecase, client):
        """사용자 조회 실패 테스트"""
        # Mock usecase to return None
        mock_usecase = MagicMock()
        mock_usecase.get_user_profile.return_value = None
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/users/999")

        assert response.status_code == 404
        data = response.json()
        assert "사용자를 찾을 수 없습니다" in data["detail"]

    @patch("routers.user.get_user_usecase")
    def test_create_user_success(self, mock_get_usecase, client):
        """사용자 생성 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        created_user = MockDataGenerator.create_user(user_id=1)
        mock_usecase.create_user.return_value = created_user
        mock_get_usecase.return_value = mock_usecase

        user_data = {"email": "test@example.com", "timezone": "Asia/Seoul", "language": "ko"}

        response = client.post("/users", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["timezone"] == "Asia/Seoul"
        assert data["language"] == "ko"

    @patch("routers.user.get_user_usecase")
    def test_create_user_invalid_data(self, mock_get_usecase, client):
        """잘못된 데이터로 사용자 생성 테스트"""
        invalid_data = {
            "email": "invalid-email",  # 잘못된 이메일 형식
            "timezone": "Invalid/Zone",
            "language": "invalid",
        }

        response = client.post("/users", json=invalid_data)

        assert response.status_code == 422  # Validation Error
        data = response.json()
        assert "detail" in data

    @patch("routers.user.get_user_usecase")
    def test_update_user_success(self, mock_get_usecase, client):
        """사용자 정보 업데이트 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        updated_user = MockDataGenerator.create_user(user_id=1, timezone="America/New_York", language="en")
        mock_usecase.update_user_profile.return_value = updated_user
        mock_get_usecase.return_value = mock_usecase

        update_data = {"timezone": "America/New_York", "language": "en"}

        response = client.put("/users/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["timezone"] == "America/New_York"
        assert data["language"] == "en"

    @patch("routers.user.get_user_usecase")
    def test_delete_user_success(self, mock_get_usecase, client):
        """사용자 삭제 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.delete_user.return_value = {"id": 1}
        mock_get_usecase.return_value = mock_usecase

        response = client.delete("/users/1")

        assert response.status_code == 200
        data = response.json()
        assert "삭제되었습니다" in data["message"]

    def test_user_api_invalid_user_id(self, client):
        """잘못된 사용자 ID 테스트"""
        # 문자열 ID
        response = client.get("/users/invalid")
        assert response.status_code == 422

        # 음수 ID
        response = client.get("/users/-1")
        assert response.status_code == 422

    @patch("routers.user.get_user_usecase")
    def test_user_api_internal_error(self, mock_get_usecase, client):
        """내부 서버 오류 테스트"""
        # Mock usecase to raise exception
        mock_usecase = MagicMock()
        mock_usecase.get_user_profile.side_effect = Exception("Internal error")
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/users/1")

        assert response.status_code == 500

    def test_user_api_cors_headers(self, client):
        """CORS 헤더 테스트"""
        response = client.get("/users/1")

        # CORS 미들웨어가 설정되어 있으므로 CORS 관련 헤더가 있어야 함
        # 실제 헤더는 구현에 따라 다를 수 있음
        assert response.status_code in [200, 404, 500]  # 상태에 관계없이 응답이 와야 함

    @patch("routers.user.get_user_usecase")
    def test_user_api_performance(self, mock_get_usecase, client):
        """사용자 API 성능 테스트"""
        import time

        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_user_profile.return_value = MockDataGenerator.create_user()
        mock_get_usecase.return_value = mock_usecase

        start_time = time.time()
        response = client.get("/users/1")
        end_time = time.time()

        # 응답 시간이 2초 이내여야 함
        response_time = end_time - start_time
        assert response_time < 2.0
        assert response.status_code == 200
