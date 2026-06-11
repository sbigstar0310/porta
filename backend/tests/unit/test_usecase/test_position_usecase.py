# tests/unit/test_usecase/test_position_usecase.py
"""
PositionUsecase 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from supabase import Client

from usecase.position_usecase import PositionUsecase
from repo.position_repo import PositionRepo
from data.models import Position
from data.schemas import PositionCreate, PositionPatch
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPositionUsecase:
    """PositionUsecase 테스트 클래스"""

    @pytest.fixture
    def mock_position_repo(self):
        """Mock PositionRepo"""
        return MagicMock(spec=PositionRepo)

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock(spec=Client)

    @pytest.fixture
    def position_usecase(self, mock_position_repo):
        """PositionUsecase 인스턴스"""
        return PositionUsecase(mock_position_repo)

    @pytest.fixture
    def sample_position(self):
        """테스트용 포지션 데이터"""
        position_data = MockDataGenerator.create_position()
        return Position(**position_data)

    @pytest.fixture
    def sample_position_create(self):
        """테스트용 포지션 생성 데이터"""
        return PositionCreate(portfolio_id=1, symbol="AAPL", shares=Decimal("10.0"), average_price=Decimal("150.00"))

    def test_position_usecase_initialization(self, mock_position_repo):
        """PositionUsecase 초기화 테스트"""
        usecase = PositionUsecase(mock_position_repo)

        assert usecase.position_repo == mock_position_repo

    def test_create_position_success(
        self, position_usecase, mock_position_repo, sample_position_create, sample_position
    ):
        """포지션 생성 성공 테스트"""
        mock_position_repo.create.return_value = sample_position

        result = position_usecase.create_position(sample_position_create)

        # 호출 검증
        mock_position_repo.create.assert_called_once_with(sample_position_create)

        # 결과 검증
        assert result == sample_position
        assert isinstance(result, Position)

    def test_create_position_failure(self, position_usecase, mock_position_repo, sample_position_create):
        """포지션 생성 실패 테스트"""
        mock_position_repo.create.return_value = None

        result = position_usecase.create_position(sample_position_create)

        # 호출 검증
        mock_position_repo.create.assert_called_once_with(sample_position_create)

        # 결과 검증
        assert result is None

    def test_get_position_success(self, position_usecase, mock_position_repo, sample_position):
        """포지션 조회 성공 테스트"""
        position_id = 1
        mock_position_repo.get_by_id.return_value = sample_position

        result = position_usecase.get_position(position_id)

        # 호출 검증
        mock_position_repo.get_by_id.assert_called_once_with(position_id)

        # 결과 검증
        assert result == sample_position

    def test_get_position_not_found(self, position_usecase, mock_position_repo):
        """포지션 조회 결과 없음 테스트"""
        position_id = 999
        mock_position_repo.get_by_id.return_value = None

        result = position_usecase.get_position(position_id)

        # 호출 검증
        mock_position_repo.get_by_id.assert_called_once_with(position_id)

        # 결과 검증
        assert result is None

    def test_get_portfolio_positions_success(self, position_usecase, mock_position_repo):
        """포트폴리오 포지션 목록 조회 성공 테스트"""
        portfolio_id = 1
        positions_data = MockDataGenerator.create_multiple_positions(5, portfolio_id)
        positions = [Position(**data) for data in positions_data]
        mock_position_repo.get_by_portfolio_id.return_value = positions

        result = position_usecase.get_portfolio_positions(portfolio_id)

        # 호출 검증
        mock_position_repo.get_by_portfolio_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert len(result) == 5
        assert all(isinstance(p, Position) for p in result)
        assert all(p.portfolio_id == portfolio_id for p in result)

    def test_get_portfolio_positions_empty(self, position_usecase, mock_position_repo):
        """포트폴리오 포지션 없음 테스트"""
        portfolio_id = 999
        mock_position_repo.get_by_portfolio_id.return_value = []

        result = position_usecase.get_portfolio_positions(portfolio_id)

        # 호출 검증
        mock_position_repo.get_by_portfolio_id.assert_called_once_with(portfolio_id)

        # 결과 검증
        assert result == []

    def test_get_position_by_symbol_success(self, position_usecase, mock_position_repo, sample_position):
        """심볼로 포지션 조회 성공 테스트"""
        portfolio_id = 1
        symbol = "AAPL"
        mock_position_repo.get_by_symbol.return_value = sample_position

        result = position_usecase.get_position_by_symbol(portfolio_id, symbol)

        # 호출 검증
        mock_position_repo.get_by_symbol.assert_called_once_with(portfolio_id, symbol)

        # 결과 검증
        assert result == sample_position
        assert result.symbol == symbol

    def test_update_position_success(self, position_usecase, mock_position_repo, sample_position):
        """포지션 업데이트 성공 테스트"""
        position_id = 1
        position_patch = PositionPatch(shares=Decimal("15.0"), current_price=Decimal("160.00"))

        # 업데이트된 포지션 데이터
        updated_data = MockDataGenerator.create_position(position_id=position_id)
        updated_data.update(position_patch.dict(exclude_unset=True))
        updated_position = Position(**updated_data)

        mock_position_repo.update.return_value = updated_position

        result = position_usecase.update_position(position_id, position_patch)

        # 호출 검증
        mock_position_repo.update.assert_called_once_with(position_patch, position_id=position_id)

        # 결과 검증
        assert result == updated_position

    def test_update_position_failure(self, position_usecase, mock_position_repo):
        """포지션 업데이트 실패 테스트"""
        position_id = 1
        position_patch = PositionPatch(shares=Decimal("15.0"))
        mock_position_repo.update.return_value = None

        result = position_usecase.update_position(position_id, position_patch)

        # 호출 검증
        mock_position_repo.update.assert_called_once_with(position_patch, position_id=position_id)

        # 결과 검증
        assert result is None

    def test_update_current_price_success(self, position_usecase, mock_position_repo, sample_position):
        """현재가 업데이트 성공 테스트"""
        position_id = 1
        new_price = Decimal("160.00")

        updated_data = MockDataGenerator.create_position(position_id=position_id)
        updated_data["current_price"] = new_price
        # 시장가치와 손익 재계산
        updated_data["market_value"] = updated_data["shares"] * new_price
        updated_data["unrealized_gain_loss"] = updated_data["shares"] * (new_price - updated_data["average_price"])
        updated_position = Position(**updated_data)

        mock_position_repo.update_current_price.return_value = updated_position

        result = position_usecase.update_current_price(position_id, new_price)

        # 호출 검증
        mock_position_repo.update_current_price.assert_called_once_with(position_id, new_price)

        # 결과 검증
        assert result == updated_position
        assert result.current_price == new_price

    def test_update_shares_success(self, position_usecase, mock_position_repo, sample_position):
        """보유 주식 수 업데이트 성공 테스트"""
        position_id = 1
        new_shares = Decimal("20.0")

        updated_data = MockDataGenerator.create_position(position_id=position_id)
        updated_data["shares"] = new_shares
        # 시장가치와 손익 재계산
        updated_data["market_value"] = new_shares * updated_data["current_price"]
        updated_data["unrealized_gain_loss"] = new_shares * (
            updated_data["current_price"] - updated_data["average_price"]
        )
        updated_position = Position(**updated_data)

        mock_position_repo.update_shares.return_value = updated_position

        result = position_usecase.update_shares(position_id, new_shares)

        # 호출 검증
        mock_position_repo.update_shares.assert_called_once_with(position_id, new_shares)

        # 결과 검증
        assert result == updated_position
        assert result.shares == new_shares

    def test_delete_position_success(self, position_usecase, mock_position_repo):
        """포지션 삭제 성공 테스트"""
        position_id = 1
        mock_position_repo.delete_by_id.return_value = {"id": position_id}

        result = position_usecase.delete_position(position_id)

        # 호출 검증
        mock_position_repo.delete_by_id.assert_called_once_with(position_id)

        # 결과 검증
        assert result["id"] == position_id

    def test_delete_position_failure(self, position_usecase, mock_position_repo):
        """포지션 삭제 실패 테스트"""
        position_id = 1
        mock_position_repo.delete_by_id.return_value = None

        result = position_usecase.delete_position(position_id)

        # 호출 검증
        mock_position_repo.delete_by_id.assert_called_once_with(position_id)

        # 결과 검증
        assert result is None

    def test_calculate_position_value_success(self, position_usecase, sample_position):
        """포지션 가치 계산 성공 테스트"""
        # 포지션 가치 = 주식 수 × 현재가
        expected_value = sample_position.shares * sample_position.current_price

        result = position_usecase.calculate_position_value(sample_position)

        # 결과 검증
        assert result == expected_value

    def test_calculate_unrealized_gain_loss_success(self, position_usecase, sample_position):
        """미실현 손익 계산 성공 테스트"""
        # 미실현 손익 = 주식 수 × (현재가 - 평균매수가)
        expected_gain_loss = sample_position.shares * (sample_position.current_price - sample_position.average_price)

        result = position_usecase.calculate_unrealized_gain_loss(sample_position)

        # 결과 검증
        assert result == expected_gain_loss

    def test_calculate_return_percentage_success(self, position_usecase, sample_position):
        """수익률 계산 성공 테스트"""
        # 수익률 = (현재가 - 평균매수가) / 평균매수가 * 100
        expected_return = (
            (sample_position.current_price - sample_position.average_price) / sample_position.average_price
        ) * 100

        result = position_usecase.calculate_return_percentage(sample_position)

        # 결과 검증
        assert abs(result - expected_return) < Decimal("0.01")  # 소수점 오차 허용

    def test_calculate_return_percentage_zero_average_price(self, position_usecase):
        """평균매수가가 0인 경우 수익률 계산 테스트"""
        position_data = MockDataGenerator.create_position()
        position_data["average_price"] = Decimal("0.0")
        position = Position(**position_data)

        result = position_usecase.calculate_return_percentage(position)

        # 0으로 나누기 방지하여 0 반환
        assert result == Decimal("0.0")

    def test_bulk_update_prices_success(self, position_usecase, mock_position_repo):
        """일괄 가격 업데이트 성공 테스트"""
        price_updates = [{"symbol": "AAPL", "price": Decimal("160.00")}, {"symbol": "MSFT", "price": Decimal("320.00")}]

        mock_position_repo.bulk_update_prices.return_value = {"updated_count": 2}

        result = position_usecase.bulk_update_prices(price_updates)

        # 호출 검증
        mock_position_repo.bulk_update_prices.assert_called_once_with(price_updates)

        # 결과 검증
        assert result["updated_count"] == 2

    def test_get_position_performance_success(self, position_usecase, mock_position_repo):
        """포지션 성과 분석 성공 테스트"""
        position_id = 1
        performance_data = {
            "id": position_id,
            "symbol": "AAPL",
            "total_return": Decimal("500.00"),
            "return_percentage": Decimal("33.33"),
            "holding_period_days": 60,
            "annualized_return": Decimal("200.00"),
        }

        mock_position_repo.get_position_performance.return_value = performance_data

        result = position_usecase.get_position_performance(position_id)

        # 호출 검증
        mock_position_repo.get_position_performance.assert_called_once_with(position_id)

        # 결과 검증
        assert result == performance_data
        assert result["return_percentage"] == Decimal("33.33")

    def test_validate_position_ownership_success(self, position_usecase, mock_position_repo, sample_position):
        """포지션 소유권 검증 성공 테스트"""
        position_id = 1
        portfolio_id = 1

        sample_position.portfolio_id = portfolio_id
        mock_position_repo.get_by_id.return_value = sample_position

        result = position_usecase.validate_position_ownership(position_id, portfolio_id)

        # 호출 검증
        mock_position_repo.get_by_id.assert_called_once_with(position_id)

        # 결과 검증
        assert result is True

    def test_validate_position_ownership_failure(self, position_usecase, mock_position_repo, sample_position):
        """포지션 소유권 검증 실패 테스트"""
        position_id = 1
        portfolio_id = 2

        sample_position.portfolio_id = 1  # 다른 포트폴리오 ID
        mock_position_repo.get_by_id.return_value = sample_position

        result = position_usecase.validate_position_ownership(position_id, portfolio_id)

        # 호출 검증
        mock_position_repo.get_by_id.assert_called_once_with(position_id)

        # 결과 검증
        assert result is False

    def test_exception_handling_in_create_position(self, position_usecase, mock_position_repo, sample_position_create):
        """포지션 생성에서 예외 처리 테스트"""
        mock_position_repo.create.side_effect = Exception("Database error")

        result = position_usecase.create_position(sample_position_create)

        # 예외 발생 시 None 반환
        assert result is None

    def test_exception_handling_in_get_position(self, position_usecase, mock_position_repo):
        """포지션 조회에서 예외 처리 테스트"""
        position_id = 1
        mock_position_repo.get_by_id.side_effect = Exception("Database error")

        result = position_usecase.get_position(position_id)

        # 예외 발생 시 None 반환
        assert result is None

    def test_position_business_logic(self, position_usecase):
        """포지션 비즈니스 로직 통합 테스트"""
        # 테스트 포지션 데이터
        position_data = MockDataGenerator.create_position(
            shares=Decimal("10.0"), average_price=Decimal("150.00"), current_price=Decimal("165.00")
        )
        position = Position(**position_data)

        # 포지션 가치 계산
        position_value = position_usecase.calculate_position_value(position)
        expected_value = Decimal("10.0") * Decimal("165.00")  # 1650.00
        assert position_value == expected_value

        # 미실현 손익 계산
        unrealized_gain = position_usecase.calculate_unrealized_gain_loss(position)
        expected_gain = Decimal("10.0") * (Decimal("165.00") - Decimal("150.00"))  # 150.00
        assert unrealized_gain == expected_gain

        # 수익률 계산
        return_percentage = position_usecase.calculate_return_percentage(position)
        expected_return = (Decimal("165.00") - Decimal("150.00")) / Decimal("150.00") * 100  # 10.00%
        assert abs(return_percentage - expected_return) < Decimal("0.01")
