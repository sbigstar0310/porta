# tests/unit/test_repo/test_user_repo.py
"""
UserRepo 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from supabase import Client

from repo.user_repo import UserRepo
from data.schemas import UserCreate, UserOut, UserPatch
from data.models import User
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestUserRepo:
    """UserRepo 테스트 클래스"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        mock_client = MagicMock(spec=Client)
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        return mock_client

    @pytest.fixture
    def user_repo(self, mock_supabase_client):
        """UserRepo 인스턴스"""
        return UserRepo(mock_supabase_client)

    @pytest.fixture
    def sample_user_create(self):
        """테스트용 사용자 생성 데이터"""
        return UserCreate(email="test@example.com", timezone="Asia/Seoul", language="ko")

    @pytest.fixture
    def sample_user_data(self):
        """테스트용 사용자 데이터"""
        return MockDataGenerator.create_user()

    def test_user_repo_initialization(self, mock_supabase_client):
        """UserRepo 초기화 테스트"""
        repo = UserRepo(mock_supabase_client)

        assert repo.db_client == mock_supabase_client
        assert repo.table_name == "users"

    def test_user_repo_with_custom_table_name(self, mock_supabase_client):
        """커스텀 테이블 이름으로 초기화 테스트"""
        custom_table = "custom_users"
        repo = UserRepo(mock_supabase_client, custom_table)

        assert repo.table_name == custom_table

    def test_create_user_success(self, user_repo, mock_supabase_client, sample_user_create, sample_user_data):
        """사용자 생성 성공 테스트"""
        # Mock 응답 설정
        mock_supabase_client.table().insert().execute.return_value.data = [sample_user_data]

        result = user_repo.create(sample_user_create)

        # 호출 검증
        mock_supabase_client.table.assert_called_with("users")
        mock_supabase_client.table().insert.assert_called_with(sample_user_create.dict())

        # 결과 검증
        assert isinstance(result, User)
        assert result.email == sample_user_data["email"]
        assert result.timezone == sample_user_data["timezone"]
        assert result.language == sample_user_data["language"]

    def test_create_user_failure(self, user_repo, mock_supabase_client, sample_user_create):
        """사용자 생성 실패 테스트"""
        # 빈 응답 설정
        mock_supabase_client.table().insert().execute.return_value.data = []

        result = user_repo.create(sample_user_create)

        assert result is None

    def test_create_user_exception_handling(self, user_repo, mock_supabase_client, sample_user_create):
        """사용자 생성 예외 처리 테스트"""
        # 예외 발생 설정
        mock_supabase_client.table().insert().execute.side_effect = Exception("DB Error")

        result = user_repo.create(sample_user_create)

        assert result is None

    def test_get_by_id_success(self, user_repo, mock_supabase_client, sample_user_data):
        """ID로 사용자 조회 성공 테스트"""
        user_id = 1
        mock_supabase_client.table().select().eq().execute.return_value.data = [sample_user_data]

        result = user_repo.get_by_id(user_id)

        # 호출 검증
        mock_supabase_client.table.assert_called_with("users")
        mock_supabase_client.table().select.assert_called_with("*")
        mock_supabase_client.table().select().eq.assert_called_with("id", user_id)

        # 결과 검증
        assert isinstance(result, User)
        assert result.id == sample_user_data["id"]
        assert result.email == sample_user_data["email"]

    def test_get_by_id_not_found(self, user_repo, mock_supabase_client):
        """ID로 사용자 조회 결과 없음 테스트"""
        user_id = 999
        mock_supabase_client.table().select().eq().execute.return_value.data = []

        result = user_repo.get_by_id(user_id)

        assert result is None

    def test_get_by_uuid_success(self, user_repo, mock_supabase_client, sample_user_data):
        """UUID로 사용자 조회 성공 테스트"""
        user_uuid = "test-uuid-123"
        mock_supabase_client.table().select().eq().execute.return_value.data = [sample_user_data]

        result = user_repo.get_by_uuid(user_uuid)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("uuid", user_uuid)

        # 결과 검증
        assert isinstance(result, User)
        assert result.uuid == sample_user_data["uuid"]

    def test_get_by_email_success(self, user_repo, mock_supabase_client, sample_user_data):
        """이메일로 사용자 조회 성공 테스트"""
        email = "test@example.com"
        mock_supabase_client.table().select().eq().execute.return_value.data = [sample_user_data]

        result = user_repo.get_by_email(email)

        # 호출 검증
        mock_supabase_client.table().select().eq.assert_called_with("email", email)

        # 결과 검증
        assert isinstance(result, User)
        assert result.email == sample_user_data["email"]

    def test_update_user_success(self, user_repo, mock_supabase_client, sample_user_data):
        """사용자 정보 업데이트 성공 테스트"""
        user_patch = UserPatch(timezone="America/New_York", language="en")
        user_id = 1

        updated_data = sample_user_data.copy()
        updated_data.update(user_patch.dict(exclude_unset=True))
        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = user_repo.update(user_patch, user_id=user_id)

        # 호출 검증
        mock_supabase_client.table().update.assert_called_with(user_patch.dict(exclude_unset=True))
        mock_supabase_client.table().update().eq.assert_called_with("id", user_id)

        # 결과 검증
        assert isinstance(result, User)
        assert result.timezone == "America/New_York"
        assert result.language == "en"

    def test_update_last_login_success(self, user_repo, mock_supabase_client, sample_user_data):
        """마지막 로그인 시간 업데이트 테스트"""
        user_id = 1
        updated_data = sample_user_data.copy()
        updated_data["last_login"] = datetime.now(timezone.utc)

        mock_supabase_client.table().update().eq().execute.return_value.data = [updated_data]

        result = user_repo.update_last_login(user_id)

        # 호출 검증 (last_login 필드가 업데이트되었는지 확인)
        update_call_args = mock_supabase_client.table().update.call_args[0][0]
        assert "last_login" in update_call_args
        mock_supabase_client.table().update().eq.assert_called_with("id", user_id)

        # 결과 검증
        assert isinstance(result, User)

    def test_delete_by_id_success(self, user_repo, mock_supabase_client):
        """사용자 삭제 성공 테스트"""
        user_id = 1
        mock_supabase_client.table().delete().eq().execute.return_value.data = [{"id": user_id}]

        result = user_repo.delete_by_id(user_id)

        # 호출 검증
        mock_supabase_client.table().delete.assert_called_with()
        mock_supabase_client.table().delete().eq.assert_called_with("id", user_id)

        # 결과 검증
        assert result == {"id": user_id}

    def test_get_all_users_success(self, user_repo, mock_supabase_client):
        """전체 사용자 조회 성공 테스트"""
        users_data = MockDataGenerator.create_multiple_users(3)
        mock_supabase_client.table().select().execute.return_value.data = users_data

        result = user_repo.get_all()

        # 호출 검증
        mock_supabase_client.table().select.assert_called_with("*")

        # 결과 검증
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(user, User) for user in result)

    def test_exception_handling_in_get_operations(self, user_repo, mock_supabase_client):
        """조회 연산에서 예외 처리 테스트"""
        mock_supabase_client.table().select().eq().execute.side_effect = Exception("DB Error")

        result = user_repo.get_by_id(1)
        assert result is None

        result = user_repo.get_by_uuid("test-uuid")
        assert result is None

        result = user_repo.get_by_email("test@example.com")
        assert result is None

    def test_user_data_validation(self, user_repo, mock_supabase_client):
        """사용자 데이터 검증 테스트"""
        # 잘못된 이메일 형식
        invalid_user_data = MockDataGenerator.create_user()
        invalid_user_data["email"] = "invalid-email"

        mock_supabase_client.table().select().eq().execute.return_value.data = [invalid_user_data]

        # Pydantic 검증으로 인해 예외가 발생하거나 None이 반환될 것으로 예상
        with pytest.raises((ValueError, Exception)):
            user_repo.get_by_id(1)
