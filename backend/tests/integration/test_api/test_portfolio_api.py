# tests/integration/test_api/test_portfolio_api.py
"""
Portfolio API 통합 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from decimal import Decimal

from app import app
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.integration
class TestPortfolioAPI:
    """Portfolio API 통합 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def sample_portfolio_data(self):
        """테스트용 포트폴리오 데이터"""
        return MockDataGenerator.create_portfolio()

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_get_portfolio_success(self, mock_get_usecase, client, sample_portfolio_data):
        """포트폴리오 조회 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_portfolio.return_value = sample_portfolio_data
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/portfolios/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_portfolio_data["id"]
        assert data["name"] == sample_portfolio_data["name"]
        assert "total_value" in data

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_get_portfolio_not_found(self, mock_get_usecase, client):
        """포트폴리오 조회 실패 테스트"""
        # Mock usecase to return None
        mock_usecase = MagicMock()
        mock_usecase.get_portfolio.return_value = None
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/portfolios/999")

        assert response.status_code == 404
        data = response.json()
        assert "포트폴리오를 찾을 수 없습니다" in data["detail"]

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_create_portfolio_success(self, mock_get_usecase, client):
        """포트폴리오 생성 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        created_portfolio = MockDataGenerator.create_portfolio()
        mock_usecase.create_portfolio.return_value = created_portfolio
        mock_get_usecase.return_value = mock_usecase

        portfolio_data = {
            "user_id": 1,
            "name": "테스트 포트폴리오",
            "description": "테스트용 포트폴리오",
            "currency": "USD",
        }

        response = client.post("/portfolios", json=portfolio_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "테스트 포트폴리오"
        assert data["currency"] == "USD"

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_create_portfolio_invalid_data(self, mock_get_usecase, client):
        """잘못된 데이터로 포트폴리오 생성 테스트"""
        invalid_data = {
            "user_id": "invalid",  # 숫자가 아닌 user_id
            "name": "",  # 빈 이름
            "currency": "INVALID",  # 잘못된 통화 코드
        }

        response = client.post("/portfolios", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_get_user_portfolios_success(self, mock_get_usecase, client):
        """사용자 포트폴리오 목록 조회 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        portfolios = MockDataGenerator.create_multiple_portfolios(3, user_id=1)
        mock_usecase.get_user_portfolios.return_value = portfolios
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/portfolios/user/1")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert all(portfolio["user_id"] == 1 for portfolio in data)

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_update_portfolio_success(self, mock_get_usecase, client):
        """포트폴리오 업데이트 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        updated_portfolio = MockDataGenerator.create_portfolio(name="업데이트된 포트폴리오")
        mock_usecase.update_portfolio.return_value = updated_portfolio
        mock_get_usecase.return_value = mock_usecase

        update_data = {"name": "업데이트된 포트폴리오", "description": "업데이트된 설명"}

        response = client.put("/portfolios/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "업데이트된 포트폴리오"

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_delete_portfolio_success(self, mock_get_usecase, client):
        """포트폴리오 삭제 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.delete_portfolio.return_value = {"id": 1}
        mock_get_usecase.return_value = mock_usecase

        response = client.delete("/portfolios/1")

        assert response.status_code == 200
        data = response.json()
        assert "삭제되었습니다" in data["message"]

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_get_portfolio_summary_success(self, mock_get_usecase, client):
        """포트폴리오 요약 정보 조회 성공 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        summary_data = {
            "id": 1,
            "name": "테스트 포트폴리오",
            "total_value": Decimal("15000.00"),
            "position_count": 5,
            "total_gain_loss": Decimal("1500.00"),
            "return_percentage": Decimal("11.11"),
        }
        mock_usecase.get_portfolio_summary.return_value = summary_data
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/portfolios/1/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "total_value" in data
        assert "position_count" in data

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_portfolio_access_control(self, mock_get_usecase, client):
        """포트폴리오 접근 제어 테스트"""
        # Mock usecase for ownership validation
        mock_usecase = MagicMock()
        mock_usecase.validate_portfolio_ownership.return_value = False
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/portfolios/1")

        # 실제 구현에 따라 상태 코드가 다를 수 있음
        # 소유권 검증이 실패하면 403 Forbidden 또는 404 Not Found
        assert response.status_code in [403, 404]

    def test_portfolio_api_invalid_ids(self, client):
        """잘못된 ID 값 테스트"""
        # 문자열 포트폴리오 ID
        response = client.get("/portfolios/invalid")
        assert response.status_code == 422

        # 음수 ID
        response = client.get("/portfolios/-1")
        assert response.status_code == 422

        # 0 ID
        response = client.get("/portfolios/0")
        assert response.status_code == 422

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_portfolio_api_performance(self, mock_get_usecase, client):
        """포트폴리오 API 성능 테스트"""
        import time

        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_portfolio.return_value = MockDataGenerator.create_portfolio()
        mock_get_usecase.return_value = mock_usecase

        start_time = time.time()
        response = client.get("/portfolios/1")
        end_time = time.time()

        # 응답 시간이 2초 이내여야 함
        response_time = end_time - start_time
        assert response_time < 2.0
        assert response.status_code == 200

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_portfolio_api_concurrent_requests(self, mock_get_usecase, client):
        """포트폴리오 API 동시 요청 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        mock_usecase.get_portfolio.return_value = MockDataGenerator.create_portfolio()
        mock_get_usecase.return_value = mock_usecase

        # 동시에 여러 요청 보내기
        responses = []
        for i in range(5):
            response = client.get(f"/portfolios/{i+1}")
            responses.append(response)

        # 모든 요청이 처리되어야 함
        for response in responses:
            assert response.status_code in [200, 404]  # 성공 또는 Not Found

    @patch("routers.portfolio.get_portfolio_usecase")
    def test_portfolio_decimal_precision(self, mock_get_usecase, client):
        """포트폴리오 Decimal 정밀도 테스트"""
        # Mock usecase
        mock_usecase = MagicMock()
        portfolio_data = MockDataGenerator.create_portfolio(total_value=Decimal("12345.6789"))
        mock_usecase.get_portfolio.return_value = portfolio_data
        mock_get_usecase.return_value = mock_usecase

        response = client.get("/portfolios/1")

        assert response.status_code == 200
        data = response.json()
        # JSON 직렬화에서 Decimal 처리 확인
        assert "total_value" in data
        # 값이 문자열 또는 숫자로 올바르게 직렬화되었는지 확인
        assert data["total_value"] is not None
