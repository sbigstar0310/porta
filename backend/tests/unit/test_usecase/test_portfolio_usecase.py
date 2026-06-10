# tests/unit/test_usecase/test_portfolio_usecase.py
"""
PortfolioUsecase 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from supabase import Client

from usecase.portfolio_usecase import PortfolioUsecase
from repo.portfolio_repo import PortfolioRepo
from data.models import Portfolio
from data.schemas import PortfolioCreate, PortfolioPatch
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPortfolioUsecase:
    """PortfolioUsecase 테스트 클래스"""

    @pytest.fixture
    def mock_portfolio_repo(self):
        """Mock PortfolioRepo"""
        return MagicMock(spec=PortfolioRepo)

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock(spec=Client)

    @pytest.fixture
    def portfolio_usecase(self, mock_portfolio_repo, mock_supabase_client):
        """PortfolioUsecase 인스턴스"""
        return PortfolioUsecase(mock_portfolio_repo, mock_supabase_client)

    @pytest.fixture
    def sample_portfolio(self):
        """테스트용 포트폴리오 데이터"""
        portfolio_data = MockDataGenerator.create_portfolio()
        return Portfolio(**portfolio_data)

    @pytest.fixture
    def sample_portfolio_create(self):
        """테스트용 포트폴리오 생성 데이터"""
        return PortfolioCreate(user_id=1, name="테스트 포트폴리오", description="테스트용 포트폴리오", currency="USD")

    def test_portfolio_usecase_initialization(self, mock_portfolio_repo, mock_supabase_client):
        """PortfolioUsecase 초기화 테스트"""
        usecase = PortfolioUsecase(mock_portfolio_repo, mock_supabase_client)

        assert usecase.portfolio_repo == mock_portfolio_repo
        assert usecase.supabase_client == mock_supabase_client

    def test_create_portfolio_success(
        self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_create, sample_portfolio
    ):
        """포트폴리오 생성 성공 테스트"""
        mock_portfolio_repo.create.return_value = sample_portfolio

        result = portfolio_usecase.create_portfolio(sample_portfolio_create)

        # 호출 검증
        mock_portfolio_repo.create.assert_called_once_with(sample_portfolio_create)

        # 결과 검증
        assert result == sample_portfolio
        assert isinstance(result, Portfolio)

    def test_create_portfolio_failure(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_create):
        """포트폴리오 생성 실패 테스트"""
        mock_portfolio_repo.create.return_value = None

        result = portfolio_usecase.create_portfolio(sample_portfolio_create)

        # 호출 검증
        mock_portfolio_repo.create.assert_called_once_with(sample_portfolio_create)

        # 결과 검증
        assert result is None

    def test_get_portfolio_success(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio):
        """포트폴리오 조회 성공 테스트"""
        portfolio_id = 1
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio

        result = portfolio_usecase.get_portfolio(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.get_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result == sample_portfolio

    def test_get_portfolio_not_found(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 조회 결과 없음 테스트"""
        portfolio_id = 999
        mock_portfolio_repo.get_by_id.return_value = None

        result = portfolio_usecase.get_portfolio(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.get_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result is None

    def test_get_user_portfolios_success(self, portfolio_usecase, mock_portfolio_repo):
        """사용자 포트폴리오 목록 조회 성공 테스트"""
        user_id = 1
        portfolios_data = MockDataGenerator.create_multiple_portfolios(3, user_id)
        portfolios = [Portfolio(**data) for data in portfolios_data]
        mock_portfolio_repo.get_by_user_id.return_value = portfolios

        result = portfolio_usecase.get_user_portfolios(user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_user_id.assert_called_once_with(user_id)

        # 결과 검증
        assert len(result) == 3
        assert all(isinstance(p, Portfolio) for p in result)
        assert all(p.user_id == user_id for p in result)

    def test_get_user_portfolios_empty(self, portfolio_usecase, mock_portfolio_repo):
        """사용자 포트폴리오 없음 테스트"""
        user_id = 999
        mock_portfolio_repo.get_by_user_id.return_value = []

        result = portfolio_usecase.get_user_portfolios(user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_user_id.assert_called_once_with(user_id)

        # 결과 검증
        assert result == []

    def test_update_portfolio_success(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio):
        """포트폴리오 업데이트 성공 테스트"""
        portfolio_id = 1
        portfolio_patch = PortfolioPatch(name="업데이트된 포트폴리오", description="업데이트된 설명")

        # 업데이트된 포트폴리오 데이터
        updated_data = MockDataGenerator.create_portfolio(portfolio_id=portfolio_id)
        updated_data.update(portfolio_patch.dict(exclude_unset=True))
        updated_portfolio = Portfolio(**updated_data)

        mock_portfolio_repo.update.return_value = updated_portfolio

        result = portfolio_usecase.update_portfolio(portfolio_id, portfolio_patch)

        # 호출 검증
        mock_portfolio_repo.update.assert_called_once_with(portfolio_patch, portfolio_id=portfolio_id)

        # 결과 검증
        assert result == updated_portfolio
        assert result.name == "업데이트된 포트폴리오"

    def test_update_portfolio_failure(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 업데이트 실패 테스트"""
        portfolio_id = 1
        portfolio_patch = PortfolioPatch(name="업데이트된 포트폴리오")
        mock_portfolio_repo.update.return_value = None

        result = portfolio_usecase.update_portfolio(portfolio_id, portfolio_patch)

        # 호출 검증
        mock_portfolio_repo.update.assert_called_once_with(portfolio_patch, portfolio_id=portfolio_id)

        # 결과 검증
        assert result is None

    def test_delete_portfolio_success(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 삭제 성공 테스트"""
        portfolio_id = 1
        mock_portfolio_repo.delete_by_id.return_value = {"id": portfolio_id}

        result = portfolio_usecase.delete_portfolio(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.delete_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result["id"] == portfolio_id

    def test_delete_portfolio_failure(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 삭제 실패 테스트"""
        portfolio_id = 1
        mock_portfolio_repo.delete_by_id.return_value = None

        result = portfolio_usecase.delete_portfolio(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.delete_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result is None

    def test_calculate_portfolio_value_success(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 가치 계산 성공 테스트"""
        portfolio_id = 1
        total_value = Decimal("15000.00")

        # Mock 포지션 데이터 (시장가치 합계)
        mock_portfolio_repo.calculate_total_value.return_value = total_value

        result = portfolio_usecase.calculate_portfolio_value(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.calculate_total_value.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result == total_value

    def test_update_portfolio_total_value_success(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio):
        """포트폴리오 총 가치 업데이트 성공 테스트"""
        portfolio_id = 1
        new_total_value = Decimal("20000.00")

        updated_data = MockDataGenerator.create_portfolio(portfolio_id=portfolio_id)
        updated_data["total_value"] = new_total_value
        updated_portfolio = Portfolio(**updated_data)

        mock_portfolio_repo.update_total_value.return_value = updated_portfolio

        result = portfolio_usecase.update_portfolio_total_value(portfolio_id, new_total_value)

        # 호출 검증
        mock_portfolio_repo.update_total_value.assert_called_once_with(portfolio_id, new_total_value)

        # 결과 검증
        assert result == updated_portfolio
        assert result.total_value == new_total_value

    def test_get_portfolio_summary_success(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 요약 정보 조회 성공 테스트"""
        portfolio_id = 1
        summary_data = {
            "id": portfolio_id,
            "name": "테스트 포트폴리오",
            "total_value": Decimal("15000.00"),
            "position_count": 5,
            "total_gain_loss": Decimal("1500.00"),
            "return_percentage": Decimal("11.11"),
        }

        mock_portfolio_repo.get_portfolio_summary.return_value = summary_data

        result = portfolio_usecase.get_portfolio_summary(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.get_portfolio_summary.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result == summary_data
        assert result["total_value"] == Decimal("15000.00")
        assert result["position_count"] == 5

    def test_get_portfolio_performance_analysis_success(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 성과 분석 성공 테스트"""
        portfolio_id = 1

        # Mock 성과 데이터
        performance_data = {
            "total_return": Decimal("2500.00"),
            "return_percentage": Decimal("20.00"),
            "best_performer": {"symbol": "AAPL", "return": Decimal("15.00")},
            "worst_performer": {"symbol": "MSFT", "return": Decimal("-5.00")},
            "asset_allocation": {"AAPL": Decimal("40.00"), "MSFT": Decimal("35.00"), "GOOGL": Decimal("25.00")},
        }

        mock_portfolio_repo.get_performance_analysis.return_value = performance_data

        result = portfolio_usecase.get_portfolio_performance_analysis(portfolio_id)

        # 호출 검증
        mock_portfolio_repo.get_performance_analysis.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result == performance_data
        assert result["return_percentage"] == Decimal("20.00")
        assert "best_performer" in result
        assert "asset_allocation" in result

    def test_validate_portfolio_ownership_success(self, portfolio_usecase, mock_portfolio_repo, sample_portfolio):
        """포트폴리오 소유권 검증 성공 테스트"""
        portfolio_id = 1
        user_id = 1

        sample_portfolio.user_id = user_id
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio

        result = portfolio_usecase.validate_portfolio_ownership(portfolio_id, user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result is True

    def test_validate_portfolio_ownership_failure_not_found(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 소유권 검증 실패 - 포트폴리오 없음"""
        portfolio_id = 999
        user_id = 1

        mock_portfolio_repo.get_by_id.return_value = None

        result = portfolio_usecase.validate_portfolio_ownership(portfolio_id, user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result is False

    def test_validate_portfolio_ownership_failure_wrong_user(
        self, portfolio_usecase, mock_portfolio_repo, sample_portfolio
    ):
        """포트폴리오 소유권 검증 실패 - 다른 사용자"""
        portfolio_id = 1
        user_id = 2

        sample_portfolio.user_id = 1  # 다른 사용자 ID
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio

        result = portfolio_usecase.validate_portfolio_ownership(portfolio_id, user_id)

        # 호출 검증
        mock_portfolio_repo.get_by_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result is False

    def test_exception_handling_in_create_portfolio(
        self, portfolio_usecase, mock_portfolio_repo, sample_portfolio_create
    ):
        """포트폴리오 생성에서 예외 처리 테스트"""
        mock_portfolio_repo.create.side_effect = Exception("Database error")

        result = portfolio_usecase.create_portfolio(sample_portfolio_create)

        # 예외 발생 시 None 반환
        assert result is None

    def test_exception_handling_in_get_portfolio(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 조회에서 예외 처리 테스트"""
        portfolio_id = 1
        mock_portfolio_repo.get_by_id.side_effect = Exception("Database error")

        result = portfolio_usecase.get_portfolio(portfolio_id)

        # 예외 발생 시 None 반환
        assert result is None

    def test_portfolio_name_validation(self, portfolio_usecase):
        """포트폴리오 이름 검증 테스트"""
        # 유효한 이름
        valid_names = ["테스트 포트폴리오", "My Portfolio", "Portfolio_2024", "포트폴리오 1번"]

        for name in valid_names:
            portfolio_create = PortfolioCreate(user_id=1, name=name, currency="USD")
            assert portfolio_create.name == name

        # 빈 이름은 검증 실패
        with pytest.raises((ValueError, Exception)):
            PortfolioCreate(user_id=1, name="", currency="USD")

    def test_currency_validation(self, portfolio_usecase):
        """통화 코드 검증 테스트"""
        valid_currencies = ["USD", "KRW", "EUR", "JPY", "GBP"]

        for currency in valid_currencies:
            portfolio_create = PortfolioCreate(user_id=1, name="테스트 포트폴리오", currency=currency)
            assert portfolio_create.currency == currency

    def test_portfolio_business_logic(self, portfolio_usecase, mock_portfolio_repo):
        """포트폴리오 비즈니스 로직 테스트"""
        portfolio_id = 1

        # 포트폴리오 재평가 (총 가치 업데이트)
        new_total_value = Decimal("18000.00")
        updated_portfolio_data = MockDataGenerator.create_portfolio(portfolio_id=portfolio_id)
        updated_portfolio_data["total_value"] = new_total_value
        updated_portfolio = Portfolio(**updated_portfolio_data)

        mock_portfolio_repo.calculate_total_value.return_value = new_total_value
        mock_portfolio_repo.update_total_value.return_value = updated_portfolio

        # 비즈니스 로직: 포트폴리오 재평가
        calculated_value = portfolio_usecase.calculate_portfolio_value(portfolio_id)
        result = portfolio_usecase.update_portfolio_total_value(portfolio_id, calculated_value)

        # 검증
        assert calculated_value == new_total_value
        assert result.total_value == new_total_value
