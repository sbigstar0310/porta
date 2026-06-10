# tests/unit/test_repo/test_transaction_repo.py
"""
TransactionRepo 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from supabase import Client

from repo.transaction_repo import TransactionRepo
from data.schemas import TransactionCreate
from data.models import Transaction
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestTransactionRepo:
    """TransactionRepo 테스트 클래스"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        mock_client = MagicMock(spec=Client)
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        return mock_client

    @pytest.fixture
    def transaction_repo(self, mock_supabase_client):
        """TransactionRepo 인스턴스"""
        return TransactionRepo(mock_supabase_client)

    @pytest.fixture
    def sample_transaction_create(self):
        """테스트용 거래 생성 데이터"""
        return TransactionCreate(
            portfolio_id=1,
            symbol="AAPL",
            transaction_type="buy",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            transaction_date=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_transaction_data(self):
        """테스트용 거래 데이터"""
        return MockDataGenerator.create_transaction()

    def test_transaction_repo_initialization(self, mock_supabase_client):
        """TransactionRepo 초기화 테스트"""
        repo = TransactionRepo(mock_supabase_client)

        assert repo.db_client == mock_supabase_client
        assert repo.table_name == "transactions"

    def test_create_transaction_success(
        self, transaction_repo, mock_supabase_client, sample_transaction_create, sample_transaction_data
    ):
        """거래 생성 성공 테스트"""
        mock_supabase_client.table().insert().execute.return_value.data = [sample_transaction_data]

        result = transaction_repo.create(sample_transaction_create)

        # 호출 검증
        mock_supabase_client.table.assert_called_with("transactions")
        mock_supabase_client.table().insert.assert_called_with(sample_transaction_create.dict())

        # 결과 검증
        assert isinstance(result, Transaction)
        assert result.symbol == sample_transaction_data["symbol"]
        assert result.transaction_type == sample_transaction_data["transaction_type"]
        assert result.portfolio_id == sample_transaction_data["portfolio_id"]

    def test_get_by_id_success(self, transaction_repo, mock_supabase_client, sample_transaction_data):
        """ID로 거래 조회 성공 테스트"""
        transaction_id = 1
        mock_supabase_client.table().select().eq().execute.return_value.data = [sample_transaction_data]

        result = transaction_repo.get_by_id(transaction_id)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("id", transaction_id)

        # 결과 검증
        assert isinstance(result, Transaction)
        assert result.id == sample_transaction_data["id"]

    def test_get_by_portfolio_id_success(self, transaction_repo, mock_supabase_client):
        """포트폴리오 ID로 거래 목록 조회 테스트"""
        portfolio_id = 1
        transactions_data = [
            MockDataGenerator.create_transaction(transaction_id=i + 1, portfolio_id=portfolio_id) for i in range(5)
        ]
        mock_supabase_client.table().select().eq().order().execute.return_value.data = transactions_data

        result = transaction_repo.get_by_portfolio_id(portfolio_id)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("portfolio_id", portfolio_id)
        mock_supabase_client.table().select().eq().order.assert_called_with("transaction_date", desc=True)

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(t, Transaction) for t in result)
        assert all(t.portfolio_id == portfolio_id for t in result)

    def test_get_by_symbol_success(self, transaction_repo, mock_supabase_client):
        """심볼로 거래 목록 조회 테스트"""
        portfolio_id = 1
        symbol = "AAPL"
        transactions_data = [
            MockDataGenerator.create_transaction(transaction_id=i + 1, portfolio_id=portfolio_id, symbol=symbol)
            for i in range(3)
        ]
        mock_supabase_client.table().select().eq().eq().order().execute.return_value.data = transactions_data

        result = transaction_repo.get_by_symbol(portfolio_id, symbol)

        # 호출 검증 (두 개의 eq 조건과 order가 사용되었는지 확인)
        assert mock_supabase_client.table().select().eq.call_count >= 2

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(t.symbol == symbol for t in result)
        assert all(t.portfolio_id == portfolio_id for t in result)

    def test_get_by_date_range_success(self, transaction_repo, mock_supabase_client):
        """날짜 범위로 거래 조회 테스트"""
        portfolio_id = 1
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)

        transactions_data = [
            MockDataGenerator.create_transaction(transaction_id=i + 1, portfolio_id=portfolio_id) for i in range(10)
        ]
        mock_supabase_client.table().select().eq().gte().lte().order().execute.return_value.data = transactions_data

        result = transaction_repo.get_by_date_range(portfolio_id, start_date, end_date)

        # 호출 검증 (eq, gte, lte, order가 사용되었는지 확인)
        mock_supabase_client.table().select().eq.assert_called_with("portfolio_id", portfolio_id)

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 10
        assert all(isinstance(t, Transaction) for t in result)

    def test_get_buy_transactions_success(self, transaction_repo, mock_supabase_client):
        """매수 거래만 조회 테스트"""
        portfolio_id = 1
        symbol = "AAPL"

        buy_transactions = [
            MockDataGenerator.create_transaction(
                transaction_id=i + 1, portfolio_id=portfolio_id, symbol=symbol, transaction_type="buy"
            )
            for i in range(3)
        ]
        mock_supabase_client.table().select().eq().eq().eq().order().execute.return_value.data = buy_transactions

        result = transaction_repo.get_buy_transactions(portfolio_id, symbol)

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(t.transaction_type == "buy" for t in result)
        assert all(t.symbol == symbol for t in result)

    def test_get_sell_transactions_success(self, transaction_repo, mock_supabase_client):
        """매도 거래만 조회 테스트"""
        portfolio_id = 1
        symbol = "AAPL"

        sell_transactions = [
            MockDataGenerator.create_transaction(
                transaction_id=i + 1, portfolio_id=portfolio_id, symbol=symbol, transaction_type="sell"
            )
            for i in range(2)
        ]
        mock_supabase_client.table().select().eq().eq().eq().order().execute.return_value.data = sell_transactions

        result = transaction_repo.get_sell_transactions(portfolio_id, symbol)

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(t.transaction_type == "sell" for t in result)
        assert all(t.symbol == symbol for t in result)

    def test_calculate_average_buy_price_success(self, transaction_repo, mock_supabase_client):
        """평균 매수가 계산 테스트"""
        portfolio_id = 1
        symbol = "AAPL"

        # Mock SQL 집계 함수 결과
        avg_price_data = [{"avg_price": Decimal("152.50")}]
        mock_supabase_client.table().select().eq().eq().eq().execute.return_value.data = avg_price_data

        result = transaction_repo.calculate_average_buy_price(portfolio_id, symbol)

        # 호출 검증 (집계 함수가 포함된 select가 사용되었는지 확인)
        mock_supabase_client.table().select.assert_called()

        # 결과 검증
        assert result == Decimal("152.50")

    def test_get_total_shares_bought_success(self, transaction_repo, mock_supabase_client):
        """총 매수 주식 수 조회 테스트"""
        portfolio_id = 1
        symbol = "AAPL"

        # Mock SQL 집계 함수 결과
        total_shares_data = [{"total_shares": Decimal("50.0")}]
        mock_supabase_client.table().select().eq().eq().eq().execute.return_value.data = total_shares_data

        result = transaction_repo.get_total_shares_bought(portfolio_id, symbol)

        # 결과 검증
        assert result == Decimal("50.0")

    def test_get_total_shares_sold_success(self, transaction_repo, mock_supabase_client):
        """총 매도 주식 수 조회 테스트"""
        portfolio_id = 1
        symbol = "AAPL"

        # Mock SQL 집계 함수 결과
        total_shares_data = [{"total_shares": Decimal("20.0")}]
        mock_supabase_client.table().select().eq().eq().eq().execute.return_value.data = total_shares_data

        result = transaction_repo.get_total_shares_sold(portfolio_id, symbol)

        # 결과 검증
        assert result == Decimal("20.0")

    def test_delete_by_id_success(self, transaction_repo, mock_supabase_client):
        """거래 삭제 성공 테스트"""
        transaction_id = 1
        mock_supabase_client.table().delete().eq().execute.return_value.data = [{"id": transaction_id}]

        result = transaction_repo.delete_by_id(transaction_id)

        # 호출 검증
        mock_supabase_client.table().delete().eq.assert_called_with("id", transaction_id)

        # 결과 검증
        assert result == {"id": transaction_id}

    def test_get_transaction_summary_success(self, transaction_repo, mock_supabase_client):
        """거래 요약 정보 조회 테스트"""
        portfolio_id = 1

        summary_data = [
            {
                "portfolio_id": portfolio_id,
                "total_transactions": 25,
                "total_buy_amount": Decimal("10000.00"),
                "total_sell_amount": Decimal("8000.00"),
                "net_amount": Decimal("2000.00"),
            }
        ]
        mock_supabase_client.table().select().eq().execute.return_value.data = summary_data

        result = transaction_repo.get_transaction_summary(portfolio_id)

        # 결과 검증
        assert result == summary_data[0]
        assert result["total_transactions"] == 25
        assert result["net_amount"] == Decimal("2000.00")

    def test_create_transaction_failure(self, transaction_repo, mock_supabase_client, sample_transaction_create):
        """거래 생성 실패 테스트"""
        mock_supabase_client.table().insert().execute.return_value.data = []

        result = transaction_repo.create(sample_transaction_create)

        assert result is None

    def test_get_by_id_not_found(self, transaction_repo, mock_supabase_client):
        """거래 조회 결과 없음 테스트"""
        transaction_id = 999
        mock_supabase_client.table().select().eq().execute.return_value.data = []

        result = transaction_repo.get_by_id(transaction_id)

        assert result is None

    def test_exception_handling(self, transaction_repo, mock_supabase_client, sample_transaction_create):
        """예외 처리 테스트"""
        mock_supabase_client.table().insert().execute.side_effect = Exception("DB Error")

        result = transaction_repo.create(sample_transaction_create)
        assert result is None

        mock_supabase_client.table().select().eq().execute.side_effect = Exception("DB Error")

        result = transaction_repo.get_by_id(1)
        assert result is None

    def test_calculate_average_buy_price_no_transactions(self, transaction_repo, mock_supabase_client):
        """매수 거래가 없는 경우 평균 매수가 계산 테스트"""
        portfolio_id = 1
        symbol = "AAPL"

        # 빈 결과
        mock_supabase_client.table().select().eq().eq().eq().execute.return_value.data = []

        result = transaction_repo.calculate_average_buy_price(portfolio_id, symbol)

        assert result == Decimal("0.0")

    def test_transaction_type_validation(self, transaction_repo, sample_transaction_create):
        """거래 타입 검증 테스트"""
        # 유효한 거래 타입들
        valid_types = ["buy", "sell"]

        for transaction_type in valid_types:
            sample_transaction_create.transaction_type = transaction_type
            assert sample_transaction_create.transaction_type in valid_types
