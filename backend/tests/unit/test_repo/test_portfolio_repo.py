# tests/unit/test_repo/test_portfolio_repo.py
"""
PortfolioRepo 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from decimal import Decimal
from supabase import Client

from repo.portfolio_repo import PortfolioRepo
from data.schemas import PortfolioCreate, PortfolioPatch
from data.models import Portfolio
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPortfolioRepo:
    """PortfolioRepo 테스트 클래스"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        mock_client = MagicMock(spec=Client)
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        return mock_client

    @pytest.fixture
    def portfolio_repo(self, mock_supabase_client):
        """PortfolioRepo 인스턴스"""
        return PortfolioRepo(mock_supabase_client)

    @pytest.fixture
    def sample_portfolio_create(self):
        """테스트용 포트폴리오 생성 데이터"""
        return PortfolioCreate(user_id=1, name="테스트 포트폴리오", description="테스트용 포트폴리오", currency="USD")

    @pytest.fixture
    def sample_portfolio_data(self):
        """테스트용 포트폴리오 데이터"""
        return MockDataGenerator.create_portfolio()

    def test_portfolio_repo_initialization(self, mock_supabase_client):
        """PortfolioRepo 초기화 테스트"""
        repo = PortfolioRepo(mock_supabase_client)

        assert repo.db_client == mock_supabase_client
        assert repo.table_name == "portfolios"

    def test_create_portfolio_success(
        self, portfolio_repo, mock_supabase_client, sample_portfolio_create, sample_portfolio_data
    ):
        """포트폴리오 생성 성공 테스트"""
        mock_supabase_client.table().insert().execute.return_value.data = [sample_portfolio_data]

        result = portfolio_repo.create(sample_portfolio_create)

        # 호출 검증
        mock_supabase_client.table.assert_called_with("portfolios")
        mock_supabase_client.table().insert.assert_called_with(sample_portfolio_create.dict())

        # 결과 검증
        assert isinstance(result, Portfolio)
        assert result.name == sample_portfolio_data["name"]
        assert result.user_id == sample_portfolio_data["user_id"]

    def test_get_by_id_success(self, portfolio_repo, mock_supabase_client, sample_portfolio_data):
        """ID로 포트폴리오 조회 성공 테스트"""
        portfolio_id = 1
        mock_supabase_client.table().select().eq().execute.return_value.data = [sample_portfolio_data]

        result = portfolio_repo.get_by_id(portfolio_id)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("id", portfolio_id)

        # 결과 검증
        assert isinstance(result, Portfolio)
        assert result.id == sample_portfolio_data["id"]

    def test_get_by_user_id_success(self, portfolio_repo, mock_supabase_client):
        """사용자 ID로 포트폴리오 목록 조회 테스트"""
        user_id = 1
        portfolios_data = MockDataGenerator.create_multiple_portfolios(3, user_id)
        mock_supabase_client.table().select().eq().execute.return_value.data = portfolios_data

        result = portfolio_repo.get_by_user_id(user_id)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("user_id", user_id)

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(p, Portfolio) for p in result)
        assert all(p.user_id == user_id for p in result)

    def test_update_portfolio_success(self, portfolio_repo, mock_supabase_client, sample_portfolio_data):
        """포트폴리오 업데이트 성공 테스트"""
        portfolio_patch = PortfolioPatch(name="업데이트된 포트폴리오", description="업데이트된 설명")
        portfolio_id = 1

        updated_data = sample_portfolio_data.copy()
        updated_data.update(portfolio_patch.dict(exclude_unset=True))
        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = portfolio_repo.update(portfolio_patch, portfolio_id=portfolio_id)

        # 호출 검증
        mock_supabase_client.table().update.assert_called_with(portfolio_patch.dict(exclude_unset=True))
        mock_supabase_client.table().update().eq.assert_called_with("id", portfolio_id)

        # 결과 검증
        assert isinstance(result, Portfolio)
        assert result.name == "업데이트된 포트폴리오"

    def test_update_total_value_success(self, portfolio_repo, mock_supabase_client, sample_portfolio_data):
        """포트폴리오 총 가치 업데이트 테스트"""
        portfolio_id = 1
        new_total_value = Decimal("15000.00")

        updated_data = sample_portfolio_data.copy()
        updated_data["total_value"] = new_total_value
        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = portfolio_repo.update_total_value(portfolio_id, new_total_value)

        # 호출 검증
        update_call_args = mock_supabase_client.table().update.call_args[0][0]
        assert update_call_args["total_value"] == new_total_value
        mock_supabase_client.table().update().eq.assert_called_with("id", portfolio_id)

        # 결과 검증
        assert isinstance(result, Portfolio)
        assert result.total_value == new_total_value

    def test_delete_by_id_success(self, portfolio_repo, mock_supabase_client):
        """포트폴리오 삭제 성공 테스트"""
        portfolio_id = 1
        mock_supabase_client.table().delete().eq().execute.return_value.data = [{"id": portfolio_id}]

        result = portfolio_repo.delete_by_id(portfolio_id)

        # 호출 검증
        mock_supabase_client.table().delete().eq.assert_called_with("id", portfolio_id)

        # 결과 검증
        assert result == {"id": portfolio_id}

    def test_get_portfolio_summary_success(self, portfolio_repo, mock_supabase_client):
        """포트폴리오 요약 정보 조회 테스트"""
        portfolio_id = 1
        summary_data = {
            "id": portfolio_id,
            "name": "테스트 포트폴리오",
            "total_value": Decimal("10000.00"),
            "position_count": 5,
            "total_gain_loss": Decimal("500.00"),
        }

        mock_supabase_client.table().select().eq().execute.return_value.data = [summary_data]

        result = portfolio_repo.get_portfolio_summary(portfolio_id)

        # 결과 검증
        assert result == summary_data

    def test_create_portfolio_failure(self, portfolio_repo, mock_supabase_client, sample_portfolio_create):
        """포트폴리오 생성 실패 테스트"""
        mock_supabase_client.table().insert().execute.return_value.data = []

        result = portfolio_repo.create(sample_portfolio_create)

        assert result is None

    def test_get_by_id_not_found(self, portfolio_repo, mock_supabase_client):
        """포트폴리오 조회 결과 없음 테스트"""
        portfolio_id = 999
        mock_supabase_client.table().select().eq().execute.return_value.data = []

        result = portfolio_repo.get_by_id(portfolio_id)

        assert result is None

    def test_get_by_user_id_empty_result(self, portfolio_repo, mock_supabase_client):
        """사용자의 포트폴리오가 없는 경우 테스트"""
        user_id = 999
        mock_supabase_client.table().select().eq().execute.return_value.data = []

        result = portfolio_repo.get_by_user_id(user_id)

        assert result == []

    def test_exception_handling(self, portfolio_repo, mock_supabase_client, sample_portfolio_create):
        """예외 처리 테스트"""
        mock_supabase_client.table().insert().execute.side_effect = Exception("DB Error")

        result = portfolio_repo.create(sample_portfolio_create)
        assert result is None

        mock_supabase_client.table().select().eq().execute.side_effect = Exception("DB Error")

        result = portfolio_repo.get_by_id(1)
        assert result is None

    def test_portfolio_with_positions_join(self, portfolio_repo, mock_supabase_client):
        """포트폴리오와 포지션 조인 조회 테스트"""
        portfolio_id = 1
        portfolio_with_positions = {
            "id": portfolio_id,
            "name": "테스트 포트폴리오",
            "positions": [
                {"symbol": "AAPL", "shares": 10, "current_price": 150.0},
                {"symbol": "MSFT", "shares": 5, "current_price": 300.0},
            ],
        }

        mock_supabase_client.table().select().eq().execute.return_value.data = [portfolio_with_positions]

        result = portfolio_repo.get_portfolio_with_positions(portfolio_id)

        # 호출 검증 (조인 쿼리가 사용되었는지 확인)
        mock_supabase_client.table().select.assert_called()

        # 결과 검증
        assert result["id"] == portfolio_id
        assert "positions" in result
        assert len(result["positions"]) == 2
