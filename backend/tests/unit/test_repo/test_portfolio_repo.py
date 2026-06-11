# tests/unit/test_repo/test_portfolio_repo.py
"""
PortfolioRepo 단위 테스트

현재 구현 기준:
- 생성자: PortfolioRepo(stock_client, db_client) — stock_client 의존성 주입
- 모든 공개 메서드는 async
- get_portfolio_by_user/get_by_id는 .single().execute() 체인 사용
- get_by_user_id는 포지션 + 실시간 시세(stock_client)로 enriched PortfolioOut 구성
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from repo.portfolio_repo import PortfolioRepo
from data.schemas import PortfolioCreate, PortfolioPatch, PortfolioOut
from data.models import Portfolio, Position
from tests.fixtures.mock_data import MockDataGenerator

UPDATED_AT = "2026-01-02T09:30:00+00:00"  # dateutil 파싱 경로용 ISO 문자열


@pytest.mark.unit
class TestPortfolioRepo:
    """PortfolioRepo 테스트 클래스"""

    @pytest.fixture
    def mock_db_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock()

    @pytest.fixture
    def mock_stock_client(self):
        """Mock StockClient (현재가 조회)"""
        mock_client = MagicMock()
        mock_client.get_stock_current_price.return_value = {"AAPL": Decimal("165.50")}
        return mock_client

    @pytest.fixture
    def portfolio_repo(self, mock_db_client, mock_stock_client):
        """PortfolioRepo 인스턴스 (Mock 의존성 직접 주입)"""
        return PortfolioRepo(stock_client=mock_stock_client, db_client=mock_db_client)

    @pytest.fixture
    def sample_portfolio_row(self):
        """테스트용 portfolios 테이블 행 (updated_at은 dateutil 파싱용 문자열)"""
        return MockDataGenerator.create_portfolio(portfolio_id=1, user_id=1, updated_at=UPDATED_AT)

    @pytest.fixture
    def sample_position_row(self):
        """테스트용 positions 테이블 행 (updated_at은 dateutil 파싱용 문자열)"""
        return MockDataGenerator.create_position(position_id=1, portfolio_id=1, ticker="AAPL", updated_at=UPDATED_AT)

    # ===== 초기화 =====

    def test_portfolio_repo_initialization(self, mock_db_client, mock_stock_client):
        """PortfolioRepo 초기화: 기본 테이블 이름은 portfolios"""
        repo = PortfolioRepo(stock_client=mock_stock_client, db_client=mock_db_client)

        assert repo.db_client is mock_db_client
        assert repo.stock_client is mock_stock_client
        assert repo.table_name == "portfolios"

    # ===== get_portfolio_by_user =====

    async def test_get_portfolio_by_user_success(self, portfolio_repo, mock_db_client, sample_portfolio_row):
        """사용자 ID로 포트폴리오 기본 정보 조회 성공"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_portfolio_row

        result = await portfolio_repo.get_portfolio_by_user(user_id=1)

        mock_db_client.table.assert_called_with("portfolios")
        select_chain.eq.assert_called_with("user_id", 1)

        assert isinstance(result, Portfolio)
        assert result.id == sample_portfolio_row["id"]
        assert result.user_id == 1
        assert result.cash == Decimal(str(sample_portfolio_row["cash"]))

    async def test_get_portfolio_by_user_not_found(self, portfolio_repo, mock_db_client):
        """포트폴리오가 없으면 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = await portfolio_repo.get_portfolio_by_user(user_id=999)

        assert result is None

    async def test_get_portfolio_by_user_exception_returns_none(self, portfolio_repo, mock_db_client):
        """조회 중 예외 발생 시 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.side_effect = Exception("DB Error")

        result = await portfolio_repo.get_portfolio_by_user(user_id=1)

        assert result is None

    # ===== get_portfolio_positions =====

    async def test_get_portfolio_positions_success(self, portfolio_repo, mock_db_client, sample_position_row):
        """포트폴리오 ID로 포지션 목록 조회 성공"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = [sample_position_row]

        result = await portfolio_repo.get_portfolio_positions(portfolio_id=1)

        mock_db_client.table.assert_called_with("positions")
        select_chain.eq.assert_called_with("portfolio_id", 1)

        assert len(result) == 1
        assert isinstance(result[0], Position)
        assert result[0].ticker == "AAPL"
        assert result[0].total_shares == Decimal("10.00")
        assert result[0].avg_buy_price == Decimal("150.00")

    async def test_get_portfolio_positions_empty(self, portfolio_repo, mock_db_client):
        """포지션이 없으면 빈 리스트 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = []

        result = await portfolio_repo.get_portfolio_positions(portfolio_id=999)

        assert result == []

    # ===== get_by_user_id (enriched) =====

    async def test_get_by_user_id_with_positions(
        self, portfolio_repo, mock_db_client, mock_stock_client, sample_portfolio_row, sample_position_row
    ):
        """포지션 보유 시 실시간 계산 필드가 포함된 PortfolioOut 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        # 포트폴리오 기본 정보 (single 체인)
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_portfolio_row
        # 포지션 목록 (plain 체인)
        select_chain.eq.return_value.execute.return_value.data = [sample_position_row]

        result = await portfolio_repo.get_by_user_id(user_id=1)

        mock_stock_client.get_stock_current_price.assert_called_once_with(["AAPL"])

        assert isinstance(result, PortfolioOut)
        assert len(result.positions) == 1
        position = result.positions[0]
        # 10주 x 165.50 = 1655.00, 원가 10주 x 150.00 = 1500.00
        assert position.current_price == Decimal("165.50")
        assert position.current_market_value == Decimal("1655.00")
        assert position.unrealized_pnl == Decimal("155.00")
        assert result.total_stock_value == Decimal("1655.00")
        assert result.total_value == Decimal(str(sample_portfolio_row["cash"])) + Decimal("1655.00")
        assert result.total_unrealized_pnl == Decimal("155.00")

    async def test_get_by_user_id_without_positions(self, portfolio_repo, mock_db_client, sample_portfolio_row):
        """포지션이 없으면 현금만 반영된 PortfolioOut 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_portfolio_row
        select_chain.eq.return_value.execute.return_value.data = []

        result = await portfolio_repo.get_by_user_id(user_id=1)

        assert isinstance(result, PortfolioOut)
        assert result.positions == []
        assert result.total_stock_value == Decimal("0.00")
        assert result.total_value == Decimal(str(sample_portfolio_row["cash"]))

    async def test_get_by_user_id_portfolio_not_found(self, portfolio_repo, mock_db_client):
        """포트폴리오가 없으면 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = await portfolio_repo.get_by_user_id(user_id=999)

        assert result is None

    # ===== get_by_id =====

    async def test_get_by_id_success(self, portfolio_repo, mock_db_client, sample_portfolio_row):
        """ID로 포트폴리오 조회 성공: PortfolioOut 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_portfolio_row

        result = await portfolio_repo.get_by_id(1)

        select_chain.eq.assert_called_with("id", 1)
        assert isinstance(result, PortfolioOut)
        assert result.id == sample_portfolio_row["id"]

    async def test_get_by_id_not_found(self, portfolio_repo, mock_db_client):
        """조회 결과 없으면 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = await portfolio_repo.get_by_id(999)

        assert result is None

    # ===== create =====

    async def test_create_portfolio_success(self, portfolio_repo, mock_db_client, sample_portfolio_row):
        """포트폴리오 생성 성공: insert 후 PortfolioOut 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [sample_portfolio_row]
        schema = PortfolioCreate(user_id=1, base_currency="USD", cash=Decimal("10000.00"))

        result = await portfolio_repo.create(schema)

        mock_db_client.table.assert_called_with("portfolios")
        mock_db_client.table.return_value.insert.assert_called_with(schema.model_dump(mode="json"))
        assert isinstance(result, PortfolioOut)
        assert result.user_id == sample_portfolio_row["user_id"]

    async def test_create_portfolio_empty_response_raises(self, portfolio_repo, mock_db_client):
        """insert 응답이 비어 있으면 ValueError 발생"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = []
        schema = PortfolioCreate(user_id=1)

        with pytest.raises(ValueError):
            await portfolio_repo.create(schema)

    # ===== update_by_user_id =====

    async def test_update_by_user_id_success(self, portfolio_repo, mock_db_client, sample_portfolio_row):
        """사용자 ID 기준 포트폴리오 업데이트 성공 (exclude_none 패치)"""
        patch_schema = PortfolioPatch(cash=Decimal("15000.00"))
        updated_row = {**sample_portfolio_row, "cash": 15000.00}
        update_chain = mock_db_client.table.return_value.update
        update_chain.return_value.eq.return_value.execute.return_value.data = [updated_row]

        result = await portfolio_repo.update_by_user_id(1, patch_schema)

        # None 필드(base_currency)는 패치에서 제외되어야 함
        update_chain.assert_called_with({"cash": 15000.0})
        update_chain.return_value.eq.assert_called_with("user_id", 1)
        assert isinstance(result, PortfolioOut)
        assert result.cash == Decimal("15000.00")

    # ===== update (의심 버그 문서화) =====

    async def test_update_raises_attribute_error_due_to_missing_id(self, portfolio_repo):
        """update(): PortfolioPatch에 id 필드가 없어 schema.id 접근 시 AttributeError

        주의: 현재 구현의 의심 버그를 그대로 검증한다 (소스 수정 금지 범위).
        """
        with pytest.raises(AttributeError):
            await portfolio_repo.update(PortfolioPatch(cash=Decimal("100.00")))

    # ===== delete_by_id =====

    async def test_delete_by_id_success(self, portfolio_repo, mock_db_client):
        """포트폴리오 삭제 성공: True 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = [{"id": 1}]

        result = await portfolio_repo.delete_by_id(1)

        delete_chain.eq.assert_called_with("id", 1)
        assert result is True

    async def test_delete_by_id_not_found(self, portfolio_repo, mock_db_client):
        """삭제 대상이 없으면 False 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = []

        result = await portfolio_repo.delete_by_id(999)

        assert result is False
