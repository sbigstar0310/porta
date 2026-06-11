# tests/unit/test_repo/test_transaction_repo.py
"""
TransactionRepo 단위 테스트

현재 구현 기준:
- 모든 공개 메서드는 async
- get_by_id()는 .single().execute() 체인 사용
- get_recent_transactions()는 .eq().gte().order() 체인으로 최근 N일 거래 조회
- 스키마 필드: ticker / transaction_type("BUY"|"SELL") / shares / price / transaction_date
"""
import pytest
from unittest.mock import MagicMock
from datetime import date
from decimal import Decimal

from repo.transaction_repo import TransactionRepo
from data.schemas import TransactionCreate, TransactionOut
from data.models import Transaction
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestTransactionRepo:
    """TransactionRepo 테스트 클래스"""

    @pytest.fixture
    def mock_db_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock()

    @pytest.fixture
    def transaction_repo(self, mock_db_client):
        """TransactionRepo 인스턴스 (Mock 클라이언트 직접 주입)"""
        return TransactionRepo(db_client=mock_db_client)

    @pytest.fixture
    def sample_transaction_row(self):
        """테스트용 transactions 테이블 행"""
        return MockDataGenerator.create_transaction(transaction_id=1, portfolio_id=1, ticker="AAPL")

    @pytest.fixture
    def sample_transaction_create(self):
        """테스트용 거래 생성 스키마"""
        return TransactionCreate(
            portfolio_id=1,
            ticker="AAPL",
            transaction_type="BUY",
            shares=Decimal("10.00"),
            price=Decimal("150.00"),
            transaction_date=date.today(),
        )

    # ===== 초기화 =====

    def test_transaction_repo_initialization(self, mock_db_client):
        """TransactionRepo 초기화: 기본 테이블 이름은 transactions"""
        repo = TransactionRepo(db_client=mock_db_client)

        assert repo.db_client is mock_db_client
        assert repo.table_name == "transactions"

    # ===== get_by_id =====

    async def test_get_by_id_success(self, transaction_repo, mock_db_client, sample_transaction_row):
        """ID로 거래 조회 성공: single 체인 사용, TransactionOut 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_transaction_row

        result = await transaction_repo.get_by_id(1)

        mock_db_client.table.assert_called_with("transactions")
        mock_db_client.table.return_value.select.assert_called_with("*")
        select_chain.eq.assert_called_with("id", 1)

        assert isinstance(result, TransactionOut)
        assert result.id == sample_transaction_row["id"]
        assert result.ticker == "AAPL"
        assert result.transaction_type == sample_transaction_row["transaction_type"]

    async def test_get_by_id_not_found(self, transaction_repo, mock_db_client):
        """조회 결과 없으면 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = await transaction_repo.get_by_id(999)

        assert result is None

    # ===== create =====

    async def test_create_transaction_success(
        self, transaction_repo, mock_db_client, sample_transaction_create, sample_transaction_row
    ):
        """거래 생성 성공: insert 후 TransactionOut 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [sample_transaction_row]

        result = await transaction_repo.create(sample_transaction_create)

        mock_db_client.table.assert_called_with("transactions")
        mock_db_client.table.return_value.insert.assert_called_with(sample_transaction_create.model_dump(mode="json"))

        assert isinstance(result, TransactionOut)
        assert result.portfolio_id == sample_transaction_row["portfolio_id"]
        assert result.ticker == "AAPL"

    async def test_create_transaction_empty_response(self, transaction_repo, mock_db_client, sample_transaction_create):
        """insert 응답이 비어 있으면 None 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = []

        result = await transaction_repo.create(sample_transaction_create)

        assert result is None

    # ===== update =====

    async def test_update_transaction_empty_response(self, transaction_repo, mock_db_client, sample_transaction_create):
        """업데이트 대상이 없으면 None 반환"""
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        result = await transaction_repo.update(999, sample_transaction_create)

        assert result is None

    async def test_update_transaction_nonempty_response_raises_type_error(
        self, transaction_repo, mock_db_client, sample_transaction_create, sample_transaction_row
    ):
        """update(): 성공 응답에서 response.data(list)를 dict처럼 언패킹해 TypeError 발생

        주의: 현재 구현의 의심 버그를 그대로 검증한다. (data = response.data 인데
        TransactionOut(**data)로 list를 언패킹 — data[0]이어야 할 것으로 보임)
        """
        update_chain = mock_db_client.table.return_value.update
        update_chain.return_value.eq.return_value.execute.return_value.data = [sample_transaction_row]

        with pytest.raises(TypeError):
            await transaction_repo.update(1, sample_transaction_create)

        update_chain.assert_called_with(sample_transaction_create.model_dump(mode="json"))
        update_chain.return_value.eq.assert_called_with("id", 1)

    # ===== delete_by_id =====

    async def test_delete_by_id_success(self, transaction_repo, mock_db_client):
        """거래 삭제 성공: True 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = [{"id": 1}]

        result = await transaction_repo.delete_by_id(1)

        delete_chain.eq.assert_called_with("id", 1)
        assert result is True

    async def test_delete_by_id_not_found(self, transaction_repo, mock_db_client):
        """삭제 대상이 없으면 False 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = []

        result = await transaction_repo.delete_by_id(999)

        assert result is False

    # ===== get_recent_transactions =====

    async def test_get_recent_transactions_success(self, transaction_repo, mock_db_client):
        """최근 거래 조회 성공: eq → gte → order 체인 및 Transaction 리스트 반환"""
        rows = [
            MockDataGenerator.create_transaction(transaction_id=i + 1, portfolio_id=1, ticker="AAPL") for i in range(3)
        ]
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = rows

        result = await transaction_repo.get_recent_transactions(portfolio_id=1, days=7)

        # 체인 호출 검증
        select_chain.eq.assert_called_with("portfolio_id", 1)
        gte_args = select_chain.eq.return_value.gte.call_args[0]
        assert gte_args[0] == "transaction_date"
        assert isinstance(gte_args[1], date)
        select_chain.eq.return_value.gte.return_value.order.assert_called_with("transaction_date", desc=True)

        # 결과 검증
        assert len(result) == 3
        assert all(isinstance(t, Transaction) for t in result)
        assert all(t.portfolio_id == 1 for t in result)

    async def test_get_recent_transactions_empty(self, transaction_repo, mock_db_client):
        """최근 거래가 없으면 빈 리스트 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = []

        result = await transaction_repo.get_recent_transactions(portfolio_id=1)

        assert result == []

    async def test_get_recent_transactions_exception_returns_empty(self, transaction_repo, mock_db_client):
        """조회 중 예외 발생 시 빈 리스트 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.gte.return_value.order.return_value.execute.side_effect = Exception("DB Error")

        result = await transaction_repo.get_recent_transactions(portfolio_id=1)

        assert result == []
