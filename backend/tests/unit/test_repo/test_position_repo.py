# tests/unit/test_repo/test_position_repo.py
"""
PositionRepo 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from supabase import Client

from repo.position_repo import PositionRepo
from data.schemas import PositionCreate, PositionPatch
from data.models import Position
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPositionRepo:
    """PositionRepo 테스트 클래스"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        mock_client = MagicMock(spec=Client)
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        return mock_client

    @pytest.fixture
    def position_repo(self, mock_supabase_client):
        """PositionRepo 인스턴스"""
        return PositionRepo(mock_supabase_client)

    @pytest.fixture
    def sample_position_create(self):
        """테스트용 포지션 생성 데이터"""
        return PositionCreate(portfolio_id=1, symbol="AAPL", shares=Decimal("10.0"), average_price=Decimal("150.00"))

    @pytest.fixture
    def sample_position_data(self):
        """테스트용 포지션 데이터"""
        return MockDataGenerator.create_position()

    def test_position_repo_initialization(self, mock_supabase_client):
        """PositionRepo 초기화 테스트"""
        repo = PositionRepo(mock_supabase_client)

        assert repo.db_client == mock_supabase_client
        assert repo.table_name == "positions"

    def test_create_position_success(
        self, position_repo, mock_supabase_client, sample_position_create, sample_position_data
    ):
        """포지션 생성 성공 테스트"""
        mock_supabase_client.table().insert().execute.return_value.data = [sample_position_data]

        result = position_repo.create(sample_position_create)

        # 호출 검증
        mock_supabase_client.table.assert_called_with("positions")
        mock_supabase_client.table().insert.assert_called_with(sample_position_create.dict())

        # 결과 검증
        assert isinstance(result, Position)
        assert result.symbol == sample_position_data["symbol"]
        assert result.portfolio_id == sample_position_data["portfolio_id"]

    def test_get_by_id_success(self, position_repo, mock_supabase_client, sample_position_data):
        """ID로 포지션 조회 성공 테스트"""
        position_id = 1
        mock_supabase_client.table().select().eq().execute.return_value.data = [sample_position_data]

        result = position_repo.get_by_id(position_id)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("id", position_id)

        # 결과 검증
        assert isinstance(result, Position)
        assert result.id == sample_position_data["id"]

    def test_get_by_portfolio_id_success(self, position_repo, mock_supabase_client):
        """포트폴리오 ID로 포지션 목록 조회 테스트"""
        portfolio_id = 1
        positions_data = MockDataGenerator.create_multiple_positions(5, portfolio_id)
        mock_supabase_client.table().select().eq().execute.return_value.data = positions_data

        result = position_repo.get_by_portfolio_id(portfolio_id)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("portfolio_id", portfolio_id)

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(p, Position) for p in result)
        assert all(p.portfolio_id == portfolio_id for p in result)

    def test_get_by_symbol_success(self, position_repo, mock_supabase_client, sample_position_data):
        """심볼로 포지션 조회 테스트"""
        portfolio_id = 1
        symbol = "AAPL"
        mock_supabase_client.table().select().eq().eq().execute.return_value.data = [sample_position_data]

        result = position_repo.get_by_symbol(portfolio_id, symbol)

        # 호출 검증 (두 개의 eq 조건이 사용되었는지 확인)
        assert mock_supabase_client.table().select().eq.call_count >= 2

        # 결과 검증
        assert isinstance(result, Position)
        assert result.symbol == symbol
        assert result.portfolio_id == portfolio_id

    def test_update_position_success(self, position_repo, mock_supabase_client, sample_position_data):
        """포지션 업데이트 성공 테스트"""
        position_patch = PositionPatch(shares=Decimal("15.0"), current_price=Decimal("160.00"))
        position_id = 1

        updated_data = sample_position_data.copy()
        updated_data.update(position_patch.dict(exclude_unset=True))
        # 시장가치와 손익 재계산
        updated_data["market_value"] = updated_data["shares"] * updated_data["current_price"]
        updated_data["unrealized_gain_loss"] = updated_data["shares"] * (
            updated_data["current_price"] - updated_data["average_price"]
        )

        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = position_repo.update(position_patch, position_id=position_id)

        # 호출 검증
        update_call_args = mock_supabase_client.table().update.call_args[0][0]
        assert "shares" in update_call_args or "current_price" in update_call_args
        mock_supabase_client.table().update().eq.assert_called_with("id", position_id)

        # 결과 검증
        assert isinstance(result, Position)

    def test_update_current_price_success(self, position_repo, mock_supabase_client, sample_position_data):
        """현재가 업데이트 테스트"""
        position_id = 1
        new_price = Decimal("160.00")

        updated_data = sample_position_data.copy()
        updated_data["current_price"] = new_price
        # 시장가치와 손익 재계산
        updated_data["market_value"] = updated_data["shares"] * new_price
        updated_data["unrealized_gain_loss"] = updated_data["shares"] * (new_price - updated_data["average_price"])

        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = position_repo.update_current_price(position_id, new_price)

        # 호출 검증
        update_call_args = mock_supabase_client.table().update.call_args[0][0]
        assert update_call_args["current_price"] == new_price
        assert "market_value" in update_call_args
        assert "unrealized_gain_loss" in update_call_args

        # 결과 검증
        assert isinstance(result, Position)
        assert result.current_price == new_price

    def test_update_shares_success(self, position_repo, mock_supabase_client, sample_position_data):
        """보유 주식 수 업데이트 테스트"""
        position_id = 1
        new_shares = Decimal("20.0")

        updated_data = sample_position_data.copy()
        updated_data["shares"] = new_shares
        # 시장가치와 손익 재계산
        updated_data["market_value"] = new_shares * updated_data["current_price"]
        updated_data["unrealized_gain_loss"] = new_shares * (
            updated_data["current_price"] - updated_data["average_price"]
        )

        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = position_repo.update_shares(position_id, new_shares)

        # 호출 검증
        update_call_args = mock_supabase_client.table().update.call_args[0][0]
        assert update_call_args["shares"] == new_shares
        assert "market_value" in update_call_args
        assert "unrealized_gain_loss" in update_call_args

        # 결과 검증
        assert isinstance(result, Position)
        assert result.shares == new_shares

    def test_delete_by_id_success(self, position_repo, mock_supabase_client):
        """포지션 삭제 성공 테스트"""
        position_id = 1
        mock_supabase_client.table().delete().eq().execute.return_value.data = [{"id": position_id}]

        result = position_repo.delete_by_id(position_id)

        # 호출 검증
        mock_supabase_client.table().delete().eq.assert_called_with("id", position_id)

        # 결과 검증
        assert result == {"id": position_id}

    def test_bulk_update_prices_success(self, position_repo, mock_supabase_client):
        """일괄 가격 업데이트 테스트"""
        price_updates = [{"symbol": "AAPL", "price": Decimal("160.00")}, {"symbol": "MSFT", "price": Decimal("320.00")}]

        # Mock 응답 설정
        mock_supabase_client.table().update().eq().execute.return_value.data = [{"updated": True}]

        result = position_repo.bulk_update_prices(price_updates)

        # 호출 검증 (각 심볼별로 업데이트가 호출되었는지 확인)
        assert mock_supabase_client.table().update.call_count == len(price_updates)

        # 결과 검증
        assert result is not None

    def test_get_position_performance_success(self, position_repo, mock_supabase_client):
        """포지션 성과 분석 조회 테스트"""
        position_id = 1
        performance_data = {
            "id": position_id,
            "symbol": "AAPL",
            "total_return": Decimal("10.50"),
            "return_percentage": Decimal("7.50"),
            "holding_period_days": 30,
        }

        mock_supabase_client.table().select().eq().execute.return_value.data = [performance_data]

        result = position_repo.get_position_performance(position_id)

        # 결과 검증
        assert result == performance_data

    def test_create_position_failure(self, position_repo, mock_supabase_client, sample_position_create):
        """포지션 생성 실패 테스트"""
        mock_supabase_client.table().insert().execute.return_value.data = []

        result = position_repo.create(sample_position_create)

        assert result is None

    def test_get_by_id_not_found(self, position_repo, mock_supabase_client):
        """포지션 조회 결과 없음 테스트"""
        position_id = 999
        mock_supabase_client.table().select().eq().execute.return_value.data = []

        result = position_repo.get_by_id(position_id)

        assert result is None

    def test_exception_handling(self, position_repo, mock_supabase_client, sample_position_create):
        """예외 처리 테스트"""
        mock_supabase_client.table().insert().execute.side_effect = Exception("DB Error")

        result = position_repo.create(sample_position_create)
        assert result is None

        mock_supabase_client.table().select().eq().execute.side_effect = Exception("DB Error")

        result = position_repo.get_by_id(1)
        assert result is None
