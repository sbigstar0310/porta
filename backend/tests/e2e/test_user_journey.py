# tests/e2e/test_user_journey.py
"""
사용자 여정 End-to-End 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from decimal import Decimal

from app import app
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.e2e
class TestUserJourney:
    """사용자 여정 End-to-End 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    @patch("routers.user.get_user_usecase")
    @patch("routers.portfolio.get_portfolio_usecase")
    @patch("routers.position.get_position_usecase")
    def test_complete_user_journey(self, mock_position_usecase, mock_portfolio_usecase, mock_user_usecase, client):
        """완전한 사용자 여정 테스트: 회원가입 -> 포트폴리오 생성 -> 포지션 추가 -> 조회"""

        # Mock 설정
        user_data = MockDataGenerator.create_user(user_id=1)
        portfolio_data = MockDataGenerator.create_portfolio(portfolio_id=1, user_id=1)
        position_data = MockDataGenerator.create_position(position_id=1, portfolio_id=1)

        mock_user_usecase_instance = MagicMock()
        mock_portfolio_usecase_instance = MagicMock()
        mock_position_usecase_instance = MagicMock()

        mock_user_usecase.return_value = mock_user_usecase_instance
        mock_portfolio_usecase.return_value = mock_portfolio_usecase_instance
        mock_position_usecase.return_value = mock_position_usecase_instance

        # 1. 사용자 생성
        mock_user_usecase_instance.create_user.return_value = user_data

        user_create_data = {"email": "test@example.com", "timezone": "Asia/Seoul", "language": "ko"}

        response = client.post("/users", json=user_create_data)
        assert response.status_code == 201
        created_user = response.json()
        user_id = created_user["id"]

        # 2. 사용자 조회
        mock_user_usecase_instance.get_user_profile.return_value = user_data

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        user_profile = response.json()
        assert user_profile["email"] == "test@example.com"

        # 3. 포트폴리오 생성
        mock_portfolio_usecase_instance.create_portfolio.return_value = portfolio_data

        portfolio_create_data = {
            "user_id": user_id,
            "name": "내 첫 포트폴리오",
            "description": "테스트용 포트폴리오",
            "currency": "USD",
        }

        response = client.post("/portfolios", json=portfolio_create_data)
        assert response.status_code == 201
        created_portfolio = response.json()
        portfolio_id = created_portfolio["id"]

        # 4. 포트폴리오 조회
        mock_portfolio_usecase_instance.get_portfolio.return_value = portfolio_data

        response = client.get(f"/portfolios/{portfolio_id}")
        assert response.status_code == 200
        portfolio_details = response.json()
        assert portfolio_details["name"] == "내 첫 포트폴리오"

        # 5. 포지션 추가
        mock_position_usecase_instance.create_position.return_value = position_data

        position_create_data = {"portfolio_id": portfolio_id, "symbol": "AAPL", "shares": 10.0, "average_price": 150.00}

        response = client.post("/positions", json=position_create_data)
        assert response.status_code == 201
        created_position = response.json()
        position_id = created_position["id"]

        # 6. 포지션 조회
        mock_position_usecase_instance.get_position.return_value = position_data

        response = client.get(f"/positions/{position_id}")
        assert response.status_code == 200
        position_details = response.json()
        assert position_details["symbol"] == "AAPL"
        assert position_details["shares"] == 10.0

        # 7. 포트폴리오의 포지션 목록 조회
        mock_position_usecase_instance.get_portfolio_positions.return_value = [position_data]

        response = client.get(f"/positions/portfolio/{portfolio_id}")
        assert response.status_code == 200
        positions = response.json()
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"

        # 8. 사용자의 포트폴리오 목록 조회
        mock_portfolio_usecase_instance.get_user_portfolios.return_value = [portfolio_data]

        response = client.get(f"/portfolios/user/{user_id}")
        assert response.status_code == 200
        user_portfolios = response.json()
        assert len(user_portfolios) == 1
        assert user_portfolios[0]["name"] == "내 첫 포트폴리오"

    @patch("routers.portfolio.get_portfolio_usecase")
    @patch("routers.position.get_position_usecase")
    def test_portfolio_management_journey(self, mock_position_usecase, mock_portfolio_usecase, client):
        """포트폴리오 관리 여정 테스트: 포트폴리오 생성 -> 여러 포지션 추가 -> 업데이트 -> 삭제"""

        # Mock 설정
        portfolio_data = MockDataGenerator.create_portfolio(portfolio_id=1, user_id=1)
        positions_data = MockDataGenerator.create_multiple_positions(3, portfolio_id=1)

        mock_portfolio_usecase_instance = MagicMock()
        mock_position_usecase_instance = MagicMock()

        mock_portfolio_usecase.return_value = mock_portfolio_usecase_instance
        mock_position_usecase.return_value = mock_position_usecase_instance

        # 1. 포트폴리오 생성
        mock_portfolio_usecase_instance.create_portfolio.return_value = portfolio_data

        portfolio_data_create = {
            "user_id": 1,
            "name": "다양한 포트폴리오",
            "description": "여러 주식을 담은 포트폴리오",
            "currency": "USD",
        }

        response = client.post("/portfolios", json=portfolio_data_create)
        assert response.status_code == 201
        portfolio_id = response.json()["id"]

        # 2. 여러 포지션 추가
        created_positions = []
        for i, position_data in enumerate(positions_data):
            mock_position_usecase_instance.create_position.return_value = position_data

            position_create_data = {
                "portfolio_id": portfolio_id,
                "symbol": position_data["symbol"],
                "shares": float(position_data["shares"]),
                "average_price": float(position_data["average_price"]),
            }

            response = client.post("/positions", json=position_create_data)
            assert response.status_code == 201
            created_positions.append(response.json())

        # 3. 포트폴리오의 모든 포지션 조회
        mock_position_usecase_instance.get_portfolio_positions.return_value = positions_data

        response = client.get(f"/positions/portfolio/{portfolio_id}")
        assert response.status_code == 200
        all_positions = response.json()
        assert len(all_positions) == 3

        # 4. 포지션 업데이트 (가격 변동)
        updated_position = positions_data[0].copy()
        updated_position["current_price"] = Decimal("165.00")
        mock_position_usecase_instance.update_position.return_value = updated_position

        update_data = {"current_price": 165.00}

        response = client.put(f"/positions/{created_positions[0]['id']}", json=update_data)
        assert response.status_code == 200
        updated_position_response = response.json()
        assert updated_position_response["current_price"] == 165.00

        # 5. 포트폴리오 요약 조회
        summary_data = {
            "id": portfolio_id,
            "name": "다양한 포트폴리오",
            "total_value": Decimal("15000.00"),
            "position_count": 3,
            "total_gain_loss": Decimal("1500.00"),
            "return_percentage": Decimal("11.11"),
        }
        mock_portfolio_usecase_instance.get_portfolio_summary.return_value = summary_data

        response = client.get(f"/portfolios/{portfolio_id}/summary")
        assert response.status_code == 200
        summary = response.json()
        assert summary["position_count"] == 3
        assert "total_value" in summary

        # 6. 포지션 삭제
        mock_position_usecase_instance.delete_position.return_value = {"id": created_positions[0]["id"]}

        response = client.delete(f"/positions/{created_positions[0]['id']}")
        assert response.status_code == 200

        # 7. 삭제 후 포지션 목록 확인
        remaining_positions = positions_data[1:]  # 첫 번째 포지션 제거
        mock_position_usecase_instance.get_portfolio_positions.return_value = remaining_positions

        response = client.get(f"/positions/portfolio/{portfolio_id}")
        assert response.status_code == 200
        remaining_positions_response = response.json()
        assert len(remaining_positions_response) == 2

    @patch("routers.user.get_user_usecase")
    def test_user_profile_management_journey(self, mock_user_usecase, client):
        """사용자 프로필 관리 여정 테스트: 생성 -> 조회 -> 업데이트 -> 설정 변경"""

        # Mock 설정
        user_data = MockDataGenerator.create_user(user_id=1)
        mock_user_usecase_instance = MagicMock()
        mock_user_usecase.return_value = mock_user_usecase_instance

        # 1. 사용자 생성
        mock_user_usecase_instance.create_user.return_value = user_data

        user_create_data = {"email": "journey@example.com", "timezone": "Asia/Seoul", "language": "ko"}

        response = client.post("/users", json=user_create_data)
        assert response.status_code == 201
        user_id = response.json()["id"]

        # 2. 프로필 조회
        mock_user_usecase_instance.get_user_profile.return_value = user_data

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        profile = response.json()
        assert profile["email"] == "journey@example.com"
        assert profile["timezone"] == "Asia/Seoul"
        assert profile["language"] == "ko"

        # 3. 프로필 업데이트 (타임존 변경)
        updated_user_data = user_data.copy()
        updated_user_data["timezone"] = "America/New_York"
        mock_user_usecase_instance.update_user_profile.return_value = updated_user_data

        update_data = {"timezone": "America/New_York"}

        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        updated_profile = response.json()
        assert updated_profile["timezone"] == "America/New_York"

        # 4. 언어 설정 변경
        updated_user_data["language"] = "en"
        mock_user_usecase_instance.update_user_profile.return_value = updated_user_data

        language_update = {"language": "en"}

        response = client.put(f"/users/{user_id}", json=language_update)
        assert response.status_code == 200
        language_updated_profile = response.json()
        assert language_updated_profile["language"] == "en"

        # 5. 최종 프로필 확인
        mock_user_usecase_instance.get_user_profile.return_value = updated_user_data

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        final_profile = response.json()
        assert final_profile["timezone"] == "America/New_York"
        assert final_profile["language"] == "en"
        assert final_profile["email"] == "journey@example.com"  # 이메일은 변경되지 않음

    def test_error_handling_journey(self, client):
        """오류 처리 여정 테스트: 잘못된 요청들의 연속"""

        # 1. 존재하지 않는 사용자 조회
        response = client.get("/users/999")
        assert response.status_code in [404, 500]  # Not Found 또는 Internal Error

        # 2. 존재하지 않는 포트폴리오 조회
        response = client.get("/portfolios/999")
        assert response.status_code in [404, 500]

        # 3. 잘못된 데이터로 사용자 생성 시도
        invalid_user_data = {"email": "invalid-email", "timezone": "Invalid/Zone", "language": "invalid-lang"}

        response = client.post("/users", json=invalid_user_data)
        assert response.status_code == 422  # Validation Error

        # 4. 잘못된 데이터로 포트폴리오 생성 시도
        invalid_portfolio_data = {"user_id": "invalid", "name": "", "currency": "INVALID"}

        response = client.post("/portfolios", json=invalid_portfolio_data)
        assert response.status_code == 422

        # 5. 잘못된 HTTP 메서드 사용
        response = client.post("/health")  # POST는 허용되지 않음
        assert response.status_code == 405  # Method Not Allowed

        # 6. 존재하지 않는 엔드포인트 접근
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_api_integration_journey(self, client):
        """API 통합 여정 테스트: 여러 엔드포인트 간의 상호작용"""

        # 1. 시스템 상태 확인
        response = client.get("/health")
        assert response.status_code == 200
        health_status = response.json()
        assert health_status["status"] == "healthy"

        # 2. DB 상태 확인
        with patch("routers.health.Database") as mock_database:
            mock_db_instance = MagicMock()
            mock_db_instance.health_check.return_value = {
                "status": "healthy",
                "connected": True,
                "timestamp": "2024-01-01T00:00:00Z",
            }
            mock_database.return_value = mock_db_instance

            response = client.get("/health/db")
            assert response.status_code == 200
            db_health = response.json()
            assert db_health["connected"] is True

        # 3. 여러 엔드포인트 순차 호출 (시스템 안정성 확인)
        endpoints = ["/health", "/health/db"]

        for endpoint in endpoints:
            if endpoint == "/health/db":
                with patch("routers.health.Database") as mock_database:
                    mock_db_instance = MagicMock()
                    mock_db_instance.health_check.return_value = {"status": "healthy", "connected": True}
                    mock_database.return_value = mock_db_instance
                    response = client.get(endpoint)
            else:
                response = client.get(endpoint)

            assert response.status_code == 200
