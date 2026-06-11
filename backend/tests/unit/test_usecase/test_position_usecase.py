# tests/unit/test_usecase/test_position_usecase.py
"""
PositionUsecase 단위 테스트
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from pydantic import ValidationError

from usecase.position_usecase import PositionUsecase
from repo.position_repo import PositionRepo
from data.schemas import PositionOut, PositionCreate, PositionPatch
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestPositionUsecase:
    """PositionUsecase 테스트 클래스"""

    @pytest.fixture
    def mock_position_repo(self):
        """Mock PositionRepo (async 메서드는 spec 덕분에 자동으로 AsyncMock이 됨)"""
        return MagicMock(spec=PositionRepo)

    @pytest.fixture
    def position_usecase(self, mock_position_repo):
        """PositionUsecase 인스턴스"""
        return PositionUsecase(mock_position_repo)

    @pytest.fixture
    def sample_position_out(self):
        """테스트용 포지션 출력 데이터"""
        position_data = MockDataGenerator.create_position()
        return PositionOut(**position_data)

    @pytest.fixture
    def sample_position_create(self):
        """테스트용 포지션 생성 데이터"""
        return PositionCreate(
            portfolio_id=1, ticker="AAPL", total_shares=Decimal("10.0"), avg_buy_price=Decimal("150.00")
        )

    def test_position_usecase_initialization(self, mock_position_repo):
        """PositionUsecase 초기화 테스트"""
        usecase = PositionUsecase(mock_position_repo)

        assert usecase.position_repo == mock_position_repo

    def test_position_usecase_initialization_default(self):
        """PositionUsecase 기본 초기화 테스트 (repo 미주입 시 None)"""
        usecase = PositionUsecase()

        assert usecase.position_repo is None

    async def test_create_position_success(
        self, position_usecase, mock_position_repo, sample_position_create, sample_position_out
    ):
        """포지션 생성 성공 테스트"""
        mock_position_repo.create.return_value = sample_position_out

        result = await position_usecase.create_position(sample_position_create)

        # 호출 검증
        mock_position_repo.create.assert_awaited_once_with(sample_position_create)

        # 결과 검증
        assert result == sample_position_out
        assert isinstance(result, PositionOut)

    async def test_create_position_failure(self, position_usecase, mock_position_repo, sample_position_create):
        """포지션 생성 실패 테스트 (repo가 None 반환)"""
        mock_position_repo.create.return_value = None

        result = await position_usecase.create_position(sample_position_create)

        # 호출 검증
        mock_position_repo.create.assert_awaited_once_with(sample_position_create)

        # 결과 검증
        assert result is None

    async def test_create_position_repo_exception_propagates(
        self, position_usecase, mock_position_repo, sample_position_create
    ):
        """포지션 생성 중 repo 예외는 그대로 전파되는 테스트 (usecase에 try/except 없음)"""
        mock_position_repo.create.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await position_usecase.create_position(sample_position_create)

    async def test_get_position_success(self, position_usecase, mock_position_repo, sample_position_out):
        """포지션 조회 성공 테스트"""
        position_id = 1
        mock_position_repo.get_by_id.return_value = sample_position_out

        result = await position_usecase.get_position(position_id)

        # 호출 검증
        mock_position_repo.get_by_id.assert_awaited_once_with(position_id)

        # 결과 검증
        assert result == sample_position_out

    async def test_get_position_not_found(self, position_usecase, mock_position_repo):
        """포지션 조회 결과 없음 테스트"""
        position_id = 999
        mock_position_repo.get_by_id.return_value = None

        result = await position_usecase.get_position(position_id)

        # 호출 검증
        mock_position_repo.get_by_id.assert_awaited_once_with(position_id)

        # 결과 검증
        assert result is None

    async def test_update_position_success(self, position_usecase, mock_position_repo):
        """포지션 업데이트 성공 테스트"""
        position_id = 1
        position_patch = PositionPatch(total_shares=Decimal("15.0"), avg_buy_price=Decimal("160.00"))

        # 업데이트된 포지션 데이터
        updated_data = MockDataGenerator.create_position(position_id=position_id)
        updated_data.update(position_patch.model_dump(exclude_unset=True))
        updated_position = PositionOut(**updated_data)

        mock_position_repo.update.return_value = updated_position

        result = await position_usecase.update_position(position_id, position_patch)

        # 호출 검증
        mock_position_repo.update.assert_awaited_once_with(position_id, position_patch)

        # 결과 검증
        assert result == updated_position
        assert result.total_shares == Decimal("15.0")
        assert result.avg_buy_price == Decimal("160.00")

    async def test_update_position_failure(self, position_usecase, mock_position_repo):
        """포지션 업데이트 실패 테스트"""
        position_id = 1
        position_patch = PositionPatch(total_shares=Decimal("15.0"))
        mock_position_repo.update.return_value = None

        result = await position_usecase.update_position(position_id, position_patch)

        # 호출 검증
        mock_position_repo.update.assert_awaited_once_with(position_id, position_patch)

        # 결과 검증
        assert result is None

    async def test_delete_position_success(self, position_usecase, mock_position_repo):
        """포지션 삭제 성공 테스트"""
        position_id = 1
        mock_position_repo.delete_by_id.return_value = True

        result = await position_usecase.delete_position(position_id)

        # 호출 검증
        mock_position_repo.delete_by_id.assert_awaited_once_with(position_id)

        # 결과 검증
        assert result is True

    async def test_delete_position_failure(self, position_usecase, mock_position_repo):
        """포지션 삭제 실패 테스트"""
        position_id = 999
        mock_position_repo.delete_by_id.return_value = False

        result = await position_usecase.delete_position(position_id)

        # 호출 검증
        mock_position_repo.delete_by_id.assert_awaited_once_with(position_id)

        # 결과 검증
        assert result is False

    def test_position_create_schema_fields(self):
        """PositionCreate 스키마 필드 검증 테스트 (ticker/total_shares/avg_buy_price)"""
        position_create = PositionCreate(
            portfolio_id=1, ticker="AAPL", total_shares=Decimal("10.0"), avg_buy_price=Decimal("150.00")
        )

        assert position_create.portfolio_id == 1
        assert position_create.ticker == "AAPL"
        assert position_create.total_shares == Decimal("10.0")
        assert position_create.avg_buy_price == Decimal("150.00")

        # 필수 필드 누락 시 검증 실패
        with pytest.raises(ValidationError):
            PositionCreate(portfolio_id=1, ticker="AAPL")

    def test_position_patch_validation(self):
        """PositionPatch 스키마 검증 테스트"""
        # 모든 필드 옵셔널
        empty_patch = PositionPatch()
        assert empty_patch.model_dump(exclude_unset=True) == {}

        # total_shares는 0 이상 허용
        patch = PositionPatch(total_shares=Decimal("0"))
        assert patch.total_shares == Decimal("0")

        # total_shares 음수는 검증 실패
        with pytest.raises(ValidationError):
            PositionPatch(total_shares=Decimal("-1"))

        # avg_buy_price는 0보다 커야 함
        with pytest.raises(ValidationError):
            PositionPatch(avg_buy_price=Decimal("0"))
