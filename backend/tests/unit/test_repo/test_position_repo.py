# tests/unit/test_repo/test_position_repo.py
"""
PositionRepo 단위 테스트

현재 구현 기준:
- 생성자: PositionRepo(db_client, stock_client) — stock_client 의존성 주입
- 모든 공개 메서드는 async
- create()는 insert 후 stock_client 시세로 enriched PositionOut 반환
- 스키마 필드: ticker / total_shares / avg_buy_price
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from repo.position_repo import PositionRepo
from data.schemas import PositionCreate, PositionPatch, PositionOut
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPositionRepo:
    """PositionRepo 테스트 클래스"""

    @pytest.fixture
    def mock_db_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock()

    @pytest.fixture
    def mock_stock_client(self):
        """Mock StockClient (현재가 조회)"""
        mock_client = MagicMock()
        mock_client.get_stock_current_price.return_value = {"AAPL": 165.50}
        return mock_client

    @pytest.fixture
    def position_repo(self, mock_db_client, mock_stock_client):
        """PositionRepo 인스턴스 (Mock 의존성 직접 주입)"""
        return PositionRepo(db_client=mock_db_client, stock_client=mock_stock_client)

    @pytest.fixture
    def sample_position_row(self):
        """테스트용 positions 테이블 행"""
        return MockDataGenerator.create_position(position_id=1, portfolio_id=1, ticker="AAPL")

    @pytest.fixture
    def sample_position_create(self):
        """테스트용 포지션 생성 스키마"""
        return PositionCreate(
            portfolio_id=1, ticker="AAPL", total_shares=Decimal("10.00"), avg_buy_price=Decimal("150.00")
        )

    # ===== 초기화 =====

    def test_position_repo_initialization(self, mock_db_client, mock_stock_client):
        """PositionRepo 초기화: 기본 테이블 이름은 positions"""
        repo = PositionRepo(db_client=mock_db_client, stock_client=mock_stock_client)

        assert repo.db_client is mock_db_client
        assert repo.stock_client is mock_stock_client
        assert repo.table_name == "positions"

    # ===== create =====

    async def test_create_position_success(
        self, position_repo, mock_db_client, mock_stock_client, sample_position_create, sample_position_row
    ):
        """포지션 생성 성공: insert 후 시세가 반영된 PositionOut 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [sample_position_row]

        result = await position_repo.create(sample_position_create)

        # insert는 mode='json' 직렬화 데이터로 호출되어야 함
        mock_db_client.table.assert_called_with("positions")
        mock_db_client.table.return_value.insert.assert_called_with(sample_position_create.model_dump(mode="json"))
        mock_stock_client.get_stock_current_price.assert_called_with(["AAPL"])

        # 결과 검증: 10주 x 165.50 = 1655.00, 원가 1500.00
        assert isinstance(result, PositionOut)
        assert result.ticker == "AAPL"
        assert result.total_shares == Decimal("10.00")
        assert result.current_price == Decimal("165.5")
        assert result.current_market_value == Decimal("1655.0")
        assert result.unrealized_pnl == Decimal("155.0")

    async def test_create_position_empty_response_raises(self, position_repo, mock_db_client, sample_position_create):
        """insert 응답이 비어 있으면 예외 발생 (response.data[0] 접근)"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = []

        with pytest.raises(IndexError):
            await position_repo.create(sample_position_create)

    async def test_create_position_db_error_propagates(self, position_repo, mock_db_client, sample_position_create):
        """insert 중 DB 예외 발생 시 그대로 전파"""
        mock_db_client.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")

        with pytest.raises(Exception, match="DB Error"):
            await position_repo.create(sample_position_create)

    # ===== get_by_id =====

    async def test_get_by_id_success(self, position_repo, mock_db_client, sample_position_row):
        """ID로 포지션 조회 성공: PositionOut 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = [sample_position_row]

        result = await position_repo.get_by_id(1)

        mock_db_client.table.return_value.select.assert_called_with("*")
        select_chain.eq.assert_called_with("id", 1)
        assert isinstance(result, PositionOut)
        assert result.id == sample_position_row["id"]
        assert result.ticker == "AAPL"

    async def test_get_by_id_not_found_returns_none(self, position_repo, mock_db_client):
        """조회 결과가 비어 있으면 None 반환 (과거 IndexError 500 버그 수정 확인)"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = []

        result = await position_repo.get_by_id(999)

        assert result is None

    # ===== update =====

    async def test_update_position_success(self, position_repo, mock_db_client, sample_position_row):
        """포지션 부분 수정 성공: exclude_unset 패치 후 PositionOut 반환"""
        patch_schema = PositionPatch(total_shares=Decimal("15.00"))
        updated_row = {**sample_position_row, "total_shares": 15.00}
        update_chain = mock_db_client.table.return_value.update
        update_chain.return_value.eq.return_value.execute.return_value.data = [updated_row]

        result = await position_repo.update(1, patch_schema)

        # 설정하지 않은 필드(ticker/avg_buy_price)는 패치에 포함되지 않아야 함
        update_chain.assert_called_with({"total_shares": 15.0})
        update_chain.return_value.eq.assert_called_with("id", 1)
        assert isinstance(result, PositionOut)
        assert result.total_shares == Decimal("15.00")

    async def test_update_position_db_error_propagates(self, position_repo, mock_db_client):
        """업데이트 중 DB 예외 발생 시 그대로 전파"""
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
            "DB Error"
        )

        with pytest.raises(Exception, match="DB Error"):
            await position_repo.update(1, PositionPatch(total_shares=Decimal("15.00")))

    # ===== delete_by_id =====

    async def test_delete_by_id_success(self, position_repo, mock_db_client):
        """포지션 삭제 성공: True 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = [{"id": 1}]

        result = await position_repo.delete_by_id(1)

        delete_chain.eq.assert_called_with("id", 1)
        assert result is True

    async def test_delete_by_id_not_found(self, position_repo, mock_db_client):
        """삭제 대상이 없으면 False 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = []

        result = await position_repo.delete_by_id(999)

        assert result is False
