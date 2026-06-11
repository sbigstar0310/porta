# tests/unit/test_usecase/test_portfolio_usecase.py
"""
PortfolioUsecase 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from pydantic import ValidationError

from usecase.portfolio_usecase import PortfolioUsecase
from repo.portfolio_repo import PortfolioRepo
from data.schemas import PortfolioOut, PortfolioCreate, PortfolioPatch
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPortfolioUsecase:
    """PortfolioUsecase 테스트 클래스"""

    @pytest.fixture
    def mock_portfolio_repo(self):
        """Mock PortfolioRepo (async 메서드는 spec 덕분에 자동으로 AsyncMock이 됨)"""
        return MagicMock(spec=PortfolioRepo)

    @pytest.fixture
    def portfolio_usecase(self, mock_portfolio_repo):
        """PortfolioUsecase 인스턴스"""
        return PortfolioUsecase(mock_portfolio_repo)

    @pytest.fixture
    def sample_portfolio_out(self):
        """테스트용 포트폴리오 출력 데이터"""
        portfolio_data = MockDataGenerator.create_portfolio()
        return PortfolioOut(**portfolio_data)

    def test_portfolio_usecase_initialization(self, mock_portfolio_repo):
        """PortfolioUsecase 초기화 테스트"""
        usecase = PortfolioUsecase(mock_portfolio_repo)

        assert usecase.portfolio_repo == mock_portfolio_repo

    async def test_get_current_portfolio_success(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_out):
        """현재 포트폴리오 조회 성공 테스트"""
        user_id = 1
        mock_portfolio_repo.get_by_user_id.return_value = sample_portfolio_out

        result = await portfolio_usecase.get_current_portfolio(user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_user_id.assert_awaited_once_with(user_id)
        mock_portfolio_repo.create.assert_not_called()  # 포트폴리오가 있으면 새로 생성하지 않음

        # 결과 검증
        assert result == sample_portfolio_out
        assert isinstance(result, PortfolioOut)

    async def test_get_current_portfolio_not_found_creates_new(
        self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_out
    ):
        """포트폴리오가 없으면 새로 생성하는 테스트"""
        user_id = 1
        mock_portfolio_repo.get_by_user_id.return_value = None
        mock_portfolio_repo.create.return_value = sample_portfolio_out

        result = await portfolio_usecase.get_current_portfolio(user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_user_id.assert_awaited_once_with(user_id)
        mock_portfolio_repo.create.assert_awaited_once_with(schema=PortfolioCreate(user_id=user_id))

        # 결과 검증 (새로 생성된 포트폴리오 반환)
        assert result == sample_portfolio_out

    def test_get_current_portfolio_sync_success(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_out):
        """현재 포트폴리오 동기 조회 성공 테스트"""
        user_id = 1
        mock_portfolio_repo.get_by_user_id.return_value = sample_portfolio_out

        result = portfolio_usecase.get_current_portfolio_sync(user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_user_id.assert_awaited_once_with(user_id)
        mock_portfolio_repo.create.assert_not_called()

        # 결과 검증
        assert result == sample_portfolio_out

    def test_get_current_portfolio_sync_not_found_creates_new(
        self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_out
    ):
        """동기 조회에서 포트폴리오가 없으면 새로 생성하는 테스트"""
        user_id = 1
        mock_portfolio_repo.get_by_user_id.return_value = None
        mock_portfolio_repo.create.return_value = sample_portfolio_out

        result = portfolio_usecase.get_current_portfolio_sync(user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_user_id.assert_awaited_once_with(user_id)
        mock_portfolio_repo.create.assert_awaited_once_with(schema=PortfolioCreate(user_id=user_id))

        # 결과 검증
        assert result == sample_portfolio_out

    async def test_update_portfolio_success(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 업데이트 성공 테스트"""
        user_id = 1
        portfolio_patch = PortfolioPatch(cash=Decimal("5000.00"), base_currency="KRW")

        # 업데이트된 포트폴리오 데이터
        updated_data = MockDataGenerator.create_portfolio(user_id=user_id)
        updated_data.update(portfolio_patch.model_dump(exclude_unset=True))
        updated_portfolio = PortfolioOut(**updated_data)

        mock_portfolio_repo.update_by_user_id.return_value = updated_portfolio

        result = await portfolio_usecase.update_portfolio(user_id, portfolio_patch)

        # 호출 검증
        mock_portfolio_repo.update_by_user_id.assert_awaited_once_with(user_id, portfolio_patch)

        # 결과 검증
        assert result == updated_portfolio
        assert result.cash == Decimal("5000.00")
        assert result.base_currency == "KRW"

    async def test_update_portfolio_failure(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 업데이트 실패 테스트"""
        user_id = 1
        portfolio_patch = PortfolioPatch(cash=Decimal("5000.00"))
        mock_portfolio_repo.update_by_user_id.return_value = None

        result = await portfolio_usecase.update_portfolio(user_id, portfolio_patch)

        # 호출 검증
        mock_portfolio_repo.update_by_user_id.assert_awaited_once_with(user_id, portfolio_patch)

        # 결과 검증
        assert result is None

    async def test_update_portfolio_repo_exception_propagates(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 업데이트 중 repo 예외는 그대로 전파되는 테스트 (usecase에 try/except 없음)"""
        user_id = 1
        portfolio_patch = PortfolioPatch(cash=Decimal("5000.00"))
        mock_portfolio_repo.update_by_user_id.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await portfolio_usecase.update_portfolio(user_id, portfolio_patch)

    def test_portfolio_create_defaults(self):
        """PortfolioCreate 기본값 테스트 (base_currency=USD, cash=0.00)"""
        portfolio_create = PortfolioCreate(user_id=1)

        assert portfolio_create.user_id == 1
        assert portfolio_create.base_currency == "USD"
        assert portfolio_create.cash == Decimal("0.00")

    def test_portfolio_create_currency_validation(self):
        """PortfolioCreate 통화 코드 검증 테스트 (ISO-4217)"""
        valid_currencies = ["USD", "KRW", "EUR", "JPY", "GBP"]

        for currency in valid_currencies:
            portfolio_create = PortfolioCreate(user_id=1, base_currency=currency)
            assert portfolio_create.base_currency == currency

        # 잘못된 통화 코드는 검증 실패
        invalid_currencies = ["usd", "DOLLAR", "U1"]
        for currency in invalid_currencies:
            with pytest.raises(ValidationError):
                PortfolioCreate(user_id=1, base_currency=currency)

    def test_portfolio_create_cash_validation(self):
        """PortfolioCreate 현금 검증 테스트 (음수 불가, 소수점 둘째 자리 반올림)"""
        # 소수점 둘째 자리로 quantize 되는지 확인
        portfolio_create = PortfolioCreate(user_id=1, cash=Decimal("1234.5678"))
        assert portfolio_create.cash == Decimal("1234.57")

        # 음수 현금은 검증 실패
        with pytest.raises(ValidationError):
            PortfolioCreate(user_id=1, cash=Decimal("-100.00"))

    def test_portfolio_patch_validation(self):
        """PortfolioPatch 스키마 검증 테스트"""
        # 모든 필드 옵셔널
        empty_patch = PortfolioPatch()
        assert empty_patch.model_dump(exclude_unset=True) == {}

        # cash quantize 확인
        patch = PortfolioPatch(cash=Decimal("99.999"))
        assert patch.cash == Decimal("100.00")

        # 잘못된 통화 코드는 검증 실패
        with pytest.raises(ValidationError):
            PortfolioPatch(base_currency="dollar")
