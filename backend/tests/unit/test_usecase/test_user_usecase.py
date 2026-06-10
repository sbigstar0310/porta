# tests/unit/test_usecase/test_user_usecase.py
"""
UserUsecase 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from supabase import Client

from usecase.user_usecase import UserUsecase
from repo.user_repo import UserRepo
from data.models import User
from data.schemas import UserCreate, UserPatch
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestUserUsecase:
    """UserUsecase 테스트 클래스"""

    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepo"""
        return MagicMock(spec=UserRepo)

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock(spec=Client)

    @pytest.fixture
    def user_usecase(self, mock_user_repo, mock_supabase_client):
        """UserUsecase 인스턴스"""
        return UserUsecase(mock_user_repo, mock_supabase_client)

    @pytest.fixture
    def sample_user(self):
        """테스트용 사용자 데이터"""
        user_data = MockDataGenerator.create_user()
        return User(**user_data)

    @pytest.fixture
    def sample_user_create(self):
        """테스트용 사용자 생성 데이터"""
        return UserCreate(email="test@example.com", timezone="Asia/Seoul", language="ko")

    def test_user_usecase_initialization(self, mock_user_repo, mock_supabase_client):
        """UserUsecase 초기화 테스트"""
        usecase = UserUsecase(mock_user_repo, mock_supabase_client)

        assert usecase.user_repo == mock_user_repo
        assert usecase.supabase_client == mock_supabase_client

    def test_get_user_profile_success(self, user_usecase, mock_user_repo, sample_user):
        """사용자 프로필 조회 성공 테스트"""
        user_id = 1
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.update_last_login.return_value = sample_user

        result = user_usecase.get_user_profile(user_id)

        # 호출 검증
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_user_repo.update_last_login.assert_called_once_with(user_id)

        # 결과 검증
        assert result == sample_user
        assert isinstance(result, User)

    def test_get_user_profile_not_found(self, user_usecase, mock_user_repo):
        """사용자 프로필 조회 결과 없음 테스트"""
        user_id = 999
        mock_user_repo.get_by_id.return_value = None

        result = user_usecase.get_user_profile(user_id)

        # 호출 검증
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_user_repo.update_last_login.assert_not_called()  # 사용자가 없으면 로그인 시간 업데이트 안함

        # 결과 검증
        assert result is None

    def test_get_user_profile_update_last_login_failure(self, user_usecase, mock_user_repo, sample_user):
        """마지막 로그인 시간 업데이트 실패 시에도 사용자 정보는 반환하는 테스트"""
        user_id = 1
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.update_last_login.return_value = None  # 업데이트 실패

        result = user_usecase.get_user_profile(user_id)

        # 호출 검증
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_user_repo.update_last_login.assert_called_once_with(user_id)

        # 결과 검증 (업데이트 실패해도 원본 사용자 정보는 반환)
        assert result == sample_user

    def test_create_user_success(self, user_usecase, mock_user_repo, sample_user_create, sample_user):
        """사용자 생성 성공 테스트"""
        mock_user_repo.create.return_value = sample_user

        result = user_usecase.create_user(sample_user_create)

        # 호출 검증
        mock_user_repo.create.assert_called_once_with(sample_user_create)

        # 결과 검증
        assert result == sample_user
        assert isinstance(result, User)

    def test_create_user_failure(self, user_usecase, mock_user_repo, sample_user_create):
        """사용자 생성 실패 테스트"""
        mock_user_repo.create.return_value = None

        result = user_usecase.create_user(sample_user_create)

        # 호출 검증
        mock_user_repo.create.assert_called_once_with(sample_user_create)

        # 결과 검증
        assert result is None

    def test_update_user_profile_success(self, user_usecase, mock_user_repo, sample_user):
        """사용자 프로필 업데이트 성공 테스트"""
        user_id = 1
        user_patch = UserPatch(timezone="America/New_York", language="en")

        # 업데이트된 사용자 데이터
        updated_user_data = MockDataGenerator.create_user(user_id=user_id)
        updated_user_data.update(user_patch.dict(exclude_unset=True))
        updated_user = User(**updated_user_data)

        mock_user_repo.update.return_value = updated_user

        result = user_usecase.update_user_profile(user_id, user_patch)

        # 호출 검증
        mock_user_repo.update.assert_called_once_with(user_patch, user_id=user_id)

        # 결과 검증
        assert result == updated_user
        assert result.timezone == "America/New_York"
        assert result.language == "en"

    def test_update_user_profile_failure(self, user_usecase, mock_user_repo):
        """사용자 프로필 업데이트 실패 테스트"""
        user_id = 1
        user_patch = UserPatch(timezone="America/New_York")
        mock_user_repo.update.return_value = None

        result = user_usecase.update_user_profile(user_id, user_patch)

        # 호출 검증
        mock_user_repo.update.assert_called_once_with(user_patch, user_id=user_id)

        # 결과 검증
        assert result is None

    def test_delete_user_success(self, user_usecase, mock_user_repo):
        """사용자 삭제 성공 테스트"""
        user_id = 1
        mock_user_repo.delete_by_id.return_value = {"id": user_id}

        result = user_usecase.delete_user(user_id)

        # 호출 검증
        mock_user_repo.delete_by_id.assert_called_once_with(user_id)

        # 결과 검증
        assert result["id"] == user_id

    def test_delete_user_failure(self, user_usecase, mock_user_repo):
        """사용자 삭제 실패 테스트"""
        user_id = 1
        mock_user_repo.delete_by_id.return_value = None

        result = user_usecase.delete_user(user_id)

        # 호출 검증
        mock_user_repo.delete_by_id.assert_called_once_with(user_id)

        # 결과 검증
        assert result is None

    def test_get_user_by_email_success(self, user_usecase, mock_user_repo, sample_user):
        """이메일로 사용자 조회 성공 테스트"""
        email = "test@example.com"
        mock_user_repo.get_by_email.return_value = sample_user

        result = user_usecase.get_user_by_email(email)

        # 호출 검증
        mock_user_repo.get_by_email.assert_called_once_with(email)

        # 결과 검증
        assert result == sample_user

    def test_get_user_by_email_not_found(self, user_usecase, mock_user_repo):
        """이메일로 사용자 조회 결과 없음 테스트"""
        email = "nonexistent@example.com"
        mock_user_repo.get_by_email.return_value = None

        result = user_usecase.get_user_by_email(email)

        # 호출 검증
        mock_user_repo.get_by_email.assert_called_once_with(email)

        # 결과 검증
        assert result is None

    def test_get_user_by_uuid_success(self, user_usecase, mock_user_repo, sample_user):
        """UUID로 사용자 조회 성공 테스트"""
        user_uuid = "test-uuid-123"
        mock_user_repo.get_by_uuid.return_value = sample_user

        result = user_usecase.get_user_by_uuid(user_uuid)

        # 호출 검증
        mock_user_repo.get_by_uuid.assert_called_once_with(user_uuid)

        # 결과 검증
        assert result == sample_user

    def test_get_all_users_success(self, user_usecase, mock_user_repo):
        """전체 사용자 조회 성공 테스트"""
        users_data = MockDataGenerator.create_multiple_users(3)
        users = [User(**user_data) for user_data in users_data]
        mock_user_repo.get_all.return_value = users

        result = user_usecase.get_all_users()

        # 호출 검증
        mock_user_repo.get_all.assert_called_once()

        # 결과 검증
        assert len(result) == 3
        assert all(isinstance(user, User) for user in result)

    def test_validate_user_permissions_success(self, user_usecase, mock_user_repo, sample_user):
        """사용자 권한 검증 성공 테스트"""
        user_id = 1
        mock_user_repo.get_by_id.return_value = sample_user

        result = user_usecase.validate_user_permissions(user_id)

        # 호출 검증
        mock_user_repo.get_by_id.assert_called_once_with(user_id)

        # 결과 검증
        assert result is True

    def test_validate_user_permissions_failure(self, user_usecase, mock_user_repo):
        """사용자 권한 검증 실패 테스트 (사용자 없음)"""
        user_id = 999
        mock_user_repo.get_by_id.return_value = None

        result = user_usecase.validate_user_permissions(user_id)

        # 호출 검증
        mock_user_repo.get_by_id.assert_called_once_with(user_id)

        # 결과 검증
        assert result is False

    def test_user_statistics_success(self, user_usecase, mock_user_repo):
        """사용자 통계 조회 성공 테스트"""
        user_id = 1

        # Mock 통계 데이터
        stats_data = {
            "total_portfolios": 3,
            "total_positions": 15,
            "total_transactions": 50,
            "total_portfolio_value": 25000.00,
        }

        mock_user_repo.get_user_statistics.return_value = stats_data

        result = user_usecase.get_user_statistics(user_id)

        # 호출 검증
        mock_user_repo.get_user_statistics.assert_called_once_with(user_id)

        # 결과 검증
        assert result == stats_data
        assert result["total_portfolios"] == 3
        assert result["total_portfolio_value"] == 25000.00

    def test_exception_handling_in_get_user_profile(self, user_usecase, mock_user_repo):
        """get_user_profile에서 예외 처리 테스트"""
        user_id = 1
        mock_user_repo.get_by_id.side_effect = Exception("Database error")

        result = user_usecase.get_user_profile(user_id)

        # 예외 발생 시 None 반환
        assert result is None

    def test_exception_handling_in_create_user(self, user_usecase, mock_user_repo, sample_user_create):
        """create_user에서 예외 처리 테스트"""
        mock_user_repo.create.side_effect = Exception("Database error")

        result = user_usecase.create_user(sample_user_create)

        # 예외 발생 시 None 반환
        assert result is None

    def test_timezone_validation(self, user_usecase):
        """타임존 검증 테스트"""
        valid_timezones = ["Asia/Seoul", "America/New_York", "Europe/London", "UTC"]
        invalid_timezones = ["Invalid/Timezone", "ABC/DEF"]

        for timezone in valid_timezones:
            user_create = UserCreate(email="test@example.com", timezone=timezone, language="ko")
            # Pydantic 검증 통과 확인
            assert user_create.timezone == timezone

        for timezone in invalid_timezones:
            with pytest.raises((ValueError, Exception)):
                UserCreate(email="test@example.com", timezone=timezone, language="ko")

    def test_language_validation(self, user_usecase):
        """언어 코드 검증 테스트"""
        valid_languages = ["ko", "en", "ja", "zh"]
        invalid_languages = ["kor", "eng", "invalid"]

        for language in valid_languages:
            user_create = UserCreate(email="test@example.com", timezone="Asia/Seoul", language=language)
            # Pydantic 검증 통과 확인
            assert user_create.language == language

        for language in invalid_languages:
            with pytest.raises((ValueError, Exception)):
                UserCreate(email="test@example.com", timezone="Asia/Seoul", language=language)
