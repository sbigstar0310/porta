# tests/unit/test_repo/test_user_repo.py
"""
UserRepo 단위 테스트

현재 구현 기준:
- 모든 메서드는 동기(sync) 메서드
- create()는 Supabase Auth sign_up + users 테이블 insert
- get_by_id()/get_by_uuid()는 .single().execute() 체인 사용
- delete_by_id()는 public.users 삭제 후 admin 클라이언트로 auth.users 삭제
"""
import pytest
from unittest.mock import MagicMock, patch

from repo.user_repo import UserRepo
from data.schemas import UserCreate, UserOut, UserPatch
from data.models import User
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestUserRepo:
    """UserRepo 테스트 클래스"""

    @pytest.fixture
    def mock_db_client(self):
        """Mock Supabase 클라이언트 (spec 없이 — auth 속성 접근 허용)"""
        mock_client = MagicMock()

        # auth.sign_up 기본 응답 (UserOut 검증을 통과하도록 실제 타입 값 고정)
        mock_session = MagicMock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"
        mock_session.expires_in = 3600
        mock_auth_user = MagicMock()
        mock_auth_user.id = "test-uuid-1"
        mock_client.auth.sign_up.return_value = MagicMock(user=mock_auth_user, session=mock_session)

        return mock_client

    @pytest.fixture
    def user_repo(self, mock_db_client):
        """UserRepo 인스턴스 (Mock 클라이언트 직접 주입)"""
        return UserRepo(db_client=mock_db_client)

    @pytest.fixture
    def sample_user_create(self):
        """테스트용 사용자 생성 스키마"""
        return UserCreate(email="test1@example.com", password="password123", timezone="Asia/Seoul", language="ko")

    @pytest.fixture
    def sample_user_row(self):
        """테스트용 users 테이블 행 데이터"""
        return MockDataGenerator.create_user(user_id=1)

    # ===== 초기화 =====

    def test_user_repo_initialization(self, mock_db_client):
        """UserRepo 초기화: 기본 테이블 이름은 users"""
        repo = UserRepo(db_client=mock_db_client)

        assert repo.db_client is mock_db_client
        assert repo.table_name == "users"

    def test_user_repo_with_custom_table_name(self, mock_db_client):
        """커스텀 테이블 이름으로 초기화"""
        repo = UserRepo(db_client=mock_db_client, table_name="custom_users")

        assert repo.table_name == "custom_users"

    # ===== create =====

    def test_create_user_success(self, user_repo, mock_db_client, sample_user_create, sample_user_row):
        """사용자 생성 성공: auth.sign_up + users insert 후 UserOut 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [sample_user_row]

        result = user_repo.create(sample_user_create)

        # auth.sign_up 호출 검증
        mock_db_client.auth.sign_up.assert_called_once()
        sign_up_payload = mock_db_client.auth.sign_up.call_args[0][0]
        assert sign_up_payload["email"] == sample_user_create.email
        assert sign_up_payload["password"] == sample_user_create.password

        # users 테이블 insert 호출 검증
        mock_db_client.table.assert_called_with("users")
        insert_payload = mock_db_client.table.return_value.insert.call_args[0][0]
        assert insert_payload["uuid"] == "test-uuid-1"
        assert insert_payload["email"] == sample_user_create.email
        assert insert_payload["email_verified"] is False

        # 결과 검증 (세션 토큰 포함)
        assert isinstance(result, UserOut)
        assert result.id == sample_user_row["id"]
        assert result.email == sample_user_row["email"]
        assert result.access_token == "test-access-token"
        assert result.refresh_token == "test-refresh-token"
        assert result.token_type == "Bearer"
        assert result.expires_in == 3600

    def test_create_user_without_session(self, user_repo, mock_db_client, sample_user_create, sample_user_row):
        """세션이 없는 가입(이메일 인증 대기): 토큰 필드가 None"""
        mock_db_client.auth.sign_up.return_value = MagicMock(user=MagicMock(id="test-uuid-1"), session=None)
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [sample_user_row]

        result = user_repo.create(sample_user_create)

        assert isinstance(result, UserOut)
        assert result.access_token is None
        assert result.refresh_token is None
        assert result.token_type is None

    def test_create_user_empty_insert_response(self, user_repo, mock_db_client, sample_user_create):
        """insert 응답이 비어 있으면 None 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = []

        result = user_repo.create(sample_user_create)

        assert result is None

    def test_create_user_exception_handling(self, user_repo, mock_db_client, sample_user_create):
        """auth.sign_up 예외 발생 시 None 반환"""
        mock_db_client.auth.sign_up.side_effect = Exception("Auth Error")

        result = user_repo.create(sample_user_create)

        assert result is None

    # ===== get_by_id / get_by_uuid =====

    def test_get_by_id_success(self, user_repo, mock_db_client, sample_user_row):
        """ID로 사용자 조회 성공: select("*").eq("id", id).single() 체인"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_user_row

        result = user_repo.get_by_id(1)

        mock_db_client.table.assert_called_with("users")
        mock_db_client.table.return_value.select.assert_called_with("*")
        select_chain.eq.assert_called_with("id", 1)

        assert isinstance(result, User)
        assert result.id == sample_user_row["id"]
        assert result.uuid == sample_user_row["uuid"]
        assert result.email == sample_user_row["email"]

    def test_get_by_id_not_found(self, user_repo, mock_db_client):
        """ID로 사용자 조회 결과 없음: None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = user_repo.get_by_id(999)

        assert result is None

    def test_get_by_id_exception_handling(self, user_repo, mock_db_client):
        """조회 중 예외 발생 시 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.side_effect = Exception("DB Error")

        result = user_repo.get_by_id(1)

        assert result is None

    def test_get_by_uuid_success(self, user_repo, mock_db_client, sample_user_row):
        """UUID로 사용자 조회 성공: UserOut 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_user_row

        result = user_repo.get_by_uuid("test-uuid-1")

        select_chain.eq.assert_called_with("uuid", "test-uuid-1")
        assert isinstance(result, UserOut)
        assert result.id == sample_user_row["id"]
        assert result.email == sample_user_row["email"]
        assert result.email_verified == sample_user_row["email_verified"]

    def test_get_by_uuid_not_found(self, user_repo, mock_db_client):
        """UUID로 사용자 조회 결과 없음: None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = user_repo.get_by_uuid("missing-uuid")

        assert result is None

    # ===== update =====

    def test_update_raises_attribute_error_due_to_missing_id_field(self, user_repo, mock_db_client, sample_user_row):
        """update(): UserPatch에 id 필드가 없어 schema.id 접근에서 AttributeError 발생

        주의: 현재 구현의 의심 버그를 그대로 검증한다.
        (UserPatch에 id가 없고, except 블록의 로그 포맷에서도 schema.id를 다시 접근해
        예외가 그대로 전파됨. 성공 시에도 response.data(list)를 dict처럼 인덱싱함)
        """
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            sample_user_row
        ]

        with pytest.raises(AttributeError):
            user_repo.update(UserPatch(timezone="America/New_York", language="en"))

    # ===== delete_by_id =====

    def test_delete_by_id_success(self, user_repo, mock_db_client, sample_user_row):
        """사용자 삭제 성공: public.users 삭제 + auth.users admin 삭제"""
        # get_by_id 체인 (single)
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = sample_user_row
        # delete 체인
        mock_db_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [
            {"id": 1}
        ]

        mock_admin_client = MagicMock()
        with patch("repo.user_repo.get_supabase_admin_client", return_value=mock_admin_client):
            result = user_repo.delete_by_id(1)

        mock_db_client.table.return_value.delete.return_value.eq.assert_called_with("id", 1)
        mock_admin_client.auth.admin.delete_user.assert_called_once_with(
            sample_user_row["uuid"], should_soft_delete=False
        )
        assert result is True

    def test_delete_by_id_user_not_found(self, user_repo, mock_db_client):
        """삭제 대상 사용자가 없으면 False 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.single.return_value.execute.return_value.data = None

        result = user_repo.delete_by_id(999)

        assert result is False

    # ===== update_last_login =====

    def test_update_last_login_success(self, user_repo, mock_db_client, sample_user_row):
        """마지막 로그인 시간 업데이트 성공: True 반환"""
        update_chain = mock_db_client.table.return_value.update
        update_chain.return_value.eq.return_value.execute.return_value.data = [sample_user_row]

        result = user_repo.update_last_login(1)

        update_chain.assert_called_with({"last_login": "NOW()"})
        update_chain.return_value.eq.assert_called_with("id", 1)
        assert result is True

    def test_update_last_login_failure(self, user_repo, mock_db_client):
        """업데이트 대상이 없으면 False 반환"""
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        result = user_repo.update_last_login(999)

        assert result is False

    # ===== update_email_verified =====

    def test_update_email_verified_success(self, user_repo, mock_db_client, sample_user_row):
        """이메일 인증 상태 업데이트 성공: True 반환"""
        update_chain = mock_db_client.table.return_value.update
        update_chain.return_value.eq.return_value.execute.return_value.data = [sample_user_row]

        result = user_repo.update_email_verified(1, verified=True)

        update_chain.assert_called_with({"email_verified": True})
        update_chain.return_value.eq.assert_called_with("id", 1)
        assert result is True

    def test_update_email_verified_user_not_found(self, user_repo, mock_db_client):
        """대상 사용자가 없으면 False 반환"""
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        result = user_repo.update_email_verified(999)

        assert result is False

    def test_update_email_verified_exception_handling(self, user_repo, mock_db_client):
        """업데이트 중 예외 발생 시 False 반환"""
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
            "DB Error"
        )

        result = user_repo.update_email_verified(1)

        assert result is False
