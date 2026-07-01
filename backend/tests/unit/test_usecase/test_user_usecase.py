# tests/unit/test_usecase/test_user_usecase.py
"""
UserUsecase 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from usecase.user_usecase import UserUsecase, EmailNotVerifiedException, InvalidRefreshTokenException
from supabase_auth.errors import AuthApiError
from repo.user_repo import UserRepo
from repo.portfolio_repo import PortfolioRepo
from repo.schedule_repo import ScheduleRepo
from data.models import User
from data.schemas import UserCreate, UserOut, PortfolioOut, PortfolioCreate, ScheduleCreate
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestUserUsecase:
    """UserUsecase 테스트 클래스"""

    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepo (모든 메서드 동기)"""
        return MagicMock(spec=UserRepo)

    @pytest.fixture
    def mock_portfolio_repo(self):
        """Mock PortfolioRepo (async 메서드는 spec 덕분에 자동으로 AsyncMock이 됨)"""
        return MagicMock(spec=PortfolioRepo)

    @pytest.fixture
    def mock_schedule_repo(self):
        """Mock ScheduleRepo (async 메서드는 spec 덕분에 자동으로 AsyncMock이 됨)"""
        return MagicMock(spec=ScheduleRepo)

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트 (auth 속성 접근을 위해 spec 없이 생성)"""
        return MagicMock()

    @pytest.fixture
    def user_usecase(self, mock_user_repo, mock_portfolio_repo, mock_schedule_repo, mock_supabase_client):
        """UserUsecase 인스턴스"""
        return UserUsecase(mock_user_repo, mock_portfolio_repo, mock_schedule_repo, mock_supabase_client)

    @pytest.fixture
    def sample_user(self):
        """테스트용 사용자 데이터 (User 모델)"""
        user_data = MockDataGenerator.create_user()
        return User(**user_data)

    @pytest.fixture
    def sample_user_out(self):
        """테스트용 사용자 출력 데이터 (UserOut 스키마)"""
        user_data = MockDataGenerator.create_user()
        return UserOut(**user_data)

    @pytest.fixture
    def sample_portfolio_out(self):
        """테스트용 포트폴리오 출력 데이터"""
        portfolio_data = MockDataGenerator.create_portfolio()
        return PortfolioOut(**portfolio_data)

    @pytest.fixture
    def mock_auth_response(self):
        """Mock Supabase 인증 응답 (user + session)"""
        auth_response = MagicMock()
        auth_response.user.id = "test-uuid-1"
        auth_response.session.access_token = "test-access-token"
        auth_response.session.refresh_token = "test-refresh-token"
        auth_response.session.expires_in = 3600
        return auth_response

    # ============= 초기화 =============

    def test_user_usecase_initialization(
        self, mock_user_repo, mock_portfolio_repo, mock_schedule_repo, mock_supabase_client
    ):
        """UserUsecase 초기화 테스트"""
        usecase = UserUsecase(mock_user_repo, mock_portfolio_repo, mock_schedule_repo, mock_supabase_client)

        assert usecase.user_repo == mock_user_repo
        assert usecase.portfolio_repo == mock_portfolio_repo
        assert usecase.schedule_repo == mock_schedule_repo
        assert usecase.supabase_client == mock_supabase_client

    # ============= get_user_profile =============

    def test_get_user_profile_success(self, user_usecase, mock_user_repo, sample_user):
        """사용자 프로필 조회 성공 테스트"""
        user_id = 1
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.update_last_login.return_value = True

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
        mock_user_repo.update_last_login.return_value = False  # 업데이트 실패

        result = user_usecase.get_user_profile(user_id)

        # 호출 검증
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_user_repo.update_last_login.assert_called_once_with(user_id)

        # 결과 검증 (업데이트 실패해도 원본 사용자 정보는 반환)
        assert result == sample_user

    def test_get_user_profile_exception_returns_none(self, user_usecase, mock_user_repo):
        """get_user_profile에서 예외 발생 시 None 반환 테스트"""
        user_id = 1
        mock_user_repo.get_by_id.side_effect = Exception("Database error")

        result = user_usecase.get_user_profile(user_id)

        # 예외 발생 시 None 반환
        assert result is None

    # ============= register_user =============

    async def test_register_user_success(
        self, user_usecase, mock_user_repo, mock_portfolio_repo, sample_user_out, sample_portfolio_out
    ):
        """사용자 등록 성공 테스트 (사용자 + 포트폴리오 생성)"""
        mock_user_repo.create.return_value = sample_user_out
        mock_portfolio_repo.create.return_value = sample_portfolio_out

        result = await user_usecase.register_user(
            email="test@example.com", password="password123", timezone="Asia/Seoul", language="ko"
        )

        # 호출 검증: user_repo.create에 UserCreate 스키마 전달
        mock_user_repo.create.assert_called_once()
        created_schema = mock_user_repo.create.call_args.kwargs["schema"]
        assert isinstance(created_schema, UserCreate)
        assert created_schema.email == "test@example.com"
        assert created_schema.password == "password123"
        assert created_schema.timezone == "Asia/Seoul"
        assert created_schema.language == "ko"

        # 호출 검증: 등록 후 포트폴리오 자동 생성
        mock_portfolio_repo.create.assert_awaited_once_with(schema=PortfolioCreate(user_id=sample_user_out.id))

        # 결과 검증
        assert result == sample_user_out

    async def test_register_user_create_failure(
        self, user_usecase, mock_user_repo, mock_portfolio_repo, mock_schedule_repo
    ):
        """사용자 등록 실패 테스트 (user_repo.create가 None 반환)"""
        mock_user_repo.create.return_value = None

        result = await user_usecase.register_user(email="test@example.com", password="password123")

        # 호출 검증: 사용자 생성 실패 시 포트폴리오/스케줄 생성 안함
        mock_user_repo.create.assert_called_once()
        mock_portfolio_repo.create.assert_not_called()
        mock_schedule_repo.create.assert_not_called()

        # 결과 검증
        assert result is None

    async def test_register_user_portfolio_failure_still_returns_user(
        self, user_usecase, mock_user_repo, mock_portfolio_repo, sample_user_out
    ):
        """포트폴리오 생성 실패해도 사용자는 반환하는 테스트"""
        mock_user_repo.create.return_value = sample_user_out
        mock_portfolio_repo.create.side_effect = Exception("Portfolio creation error")

        result = await user_usecase.register_user(email="test@example.com", password="password123")

        # 결과 검증 (포트폴리오 생성 실패해도 사용자 반환)
        assert result == sample_user_out

    async def test_register_user_creates_default_schedule(
        self, user_usecase, mock_user_repo, mock_portfolio_repo, mock_schedule_repo, sample_user_out
    ):
        """회원가입 시 기본 보고서 스케줄(09:00, 유저 timezone, enabled)이 생성되는 테스트"""
        mock_user_repo.create.return_value = sample_user_out

        result = await user_usecase.register_user(
            email="test@example.com", password="password123", timezone="Asia/Seoul", language="ko"
        )

        # 호출 검증: 기본 스케줄 생성 (매일 09:00, 요청 timezone, 활성)
        mock_schedule_repo.create.assert_awaited_once_with(
            schema=ScheduleCreate(
                user_id=sample_user_out.id,
                hour=9,
                minute=0,
                timezone="Asia/Seoul",
                enabled=True,
            )
        )

        # 결과 검증
        assert result == sample_user_out

    async def test_register_user_schedule_failure_still_returns_user(
        self, user_usecase, mock_user_repo, mock_portfolio_repo, mock_schedule_repo, sample_user_out
    ):
        """기본 스케줄 생성 실패해도 사용자는 반환하는 테스트"""
        mock_user_repo.create.return_value = sample_user_out
        mock_schedule_repo.create.side_effect = Exception("Schedule creation error")

        result = await user_usecase.register_user(email="test@example.com", password="password123")

        # 결과 검증 (스케줄 생성 실패해도 사용자 반환)
        assert result == sample_user_out

    async def test_register_user_exception_returns_none(self, user_usecase, mock_user_repo):
        """register_user에서 예외 발생 시 None 반환 테스트"""
        mock_user_repo.create.side_effect = Exception("Database error")

        result = await user_usecase.register_user(email="test@example.com", password="password123")

        # 예외 발생 시 None 반환
        assert result is None

    # ============= login =============

    def test_login_success(
        self, user_usecase, mock_user_repo, mock_supabase_client, mock_auth_response, sample_user_out
    ):
        """로그인 성공 테스트 (인증 토큰 포함 UserOut 반환)"""
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_user_repo.get_by_uuid.return_value = sample_user_out
        mock_user_repo.update_last_login.return_value = True

        result = user_usecase.login("test@example.com", "password123")

        # 호출 검증
        mock_supabase_client.auth.sign_in_with_password.assert_called_once_with(
            {"email": "test@example.com", "password": "password123"}
        )
        mock_user_repo.get_by_uuid.assert_called_once_with(mock_auth_response.user.id)
        mock_user_repo.update_last_login.assert_called_once_with(sample_user_out.id)

        # 결과 검증 (토큰 정보 포함)
        assert isinstance(result, UserOut)
        assert result.id == sample_user_out.id
        assert result.email == sample_user_out.email
        assert result.access_token == "test-access-token"
        assert result.refresh_token == "test-refresh-token"
        assert result.token_type == "Bearer"
        assert result.expires_in == 3600

    def test_login_no_session_returns_user_without_tokens(
        self, user_usecase, mock_user_repo, mock_supabase_client, mock_auth_response, sample_user_out
    ):
        """세션이 없는 경우 토큰 없이 사용자 정보만 반환하는 테스트"""
        mock_auth_response.session = None
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_user_repo.get_by_uuid.return_value = sample_user_out
        mock_user_repo.update_last_login.return_value = True

        result = user_usecase.login("test@example.com", "password123")

        # 결과 검증 (토큰 없음)
        assert isinstance(result, UserOut)
        assert result.access_token is None
        assert result.refresh_token is None

    def test_login_auth_failure_raises(self, user_usecase, mock_supabase_client):
        """Supabase 인증 실패 시 예외가 전파되는 테스트"""
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

        with pytest.raises(Exception, match="Invalid login credentials"):
            user_usecase.login("test@example.com", "wrong-password")

    def test_login_email_not_verified_raises(self, user_usecase, mock_supabase_client):
        """이메일 미인증 시 EmailNotVerifiedException 발생 테스트"""
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Email not confirmed")

        with pytest.raises(EmailNotVerifiedException):
            user_usecase.login("test@example.com", "password123")

    def test_login_no_auth_user_raises(self, user_usecase, mock_supabase_client, mock_auth_response):
        """인증 응답에 사용자 정보가 없으면 예외 발생 테스트"""
        mock_auth_response.user = None
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response

        with pytest.raises(Exception):
            user_usecase.login("test@example.com", "password123")

    def test_login_db_user_not_found_returns_none(
        self, user_usecase, mock_user_repo, mock_supabase_client, mock_auth_response
    ):
        """인증은 성공했지만 DB에 사용자가 없으면 None 반환 테스트"""
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_user_repo.get_by_uuid.return_value = None

        result = user_usecase.login("test@example.com", "password123")

        # 결과 검증
        assert result is None

    def test_login_update_last_login_failure_returns_none(
        self, user_usecase, mock_user_repo, mock_supabase_client, mock_auth_response, sample_user_out
    ):
        """로그인 시간 업데이트 실패 시 None 반환 테스트"""
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_user_repo.get_by_uuid.return_value = sample_user_out
        mock_user_repo.update_last_login.return_value = False

        result = user_usecase.login("test@example.com", "password123")

        # 결과 검증
        assert result is None

    # ============= sign_out =============

    def test_sign_out_success(self, user_usecase, mock_supabase_client):
        """로그아웃 성공 테스트"""
        user_usecase.sign_out()

        # 호출 검증
        mock_supabase_client.auth.sign_out.assert_called_once()

    def test_sign_out_exception_swallowed(self, user_usecase, mock_supabase_client):
        """로그아웃 중 예외는 삼켜지는 테스트"""
        mock_supabase_client.auth.sign_out.side_effect = Exception("Sign out error")

        # 예외가 전파되지 않아야 함
        user_usecase.sign_out()

    # ============= delete_user =============

    def test_delete_user_success(self, user_usecase, mock_user_repo):
        """사용자 삭제 성공 테스트"""
        user_id = 1
        mock_user_repo.delete_by_id.return_value = True

        user_usecase.delete_user(user_id)

        # 호출 검증
        mock_user_repo.delete_by_id.assert_called_once_with(user_id)

    def test_delete_user_exception_swallowed(self, user_usecase, mock_user_repo):
        """사용자 삭제 중 예외는 삼켜지는 테스트"""
        user_id = 1
        mock_user_repo.delete_by_id.side_effect = Exception("Delete error")

        # 예외가 전파되지 않아야 함
        user_usecase.delete_user(user_id)

        mock_user_repo.delete_by_id.assert_called_once_with(user_id)

    # ============= resend_verification_email =============

    def test_resend_verification_email_success(self, user_usecase, mock_supabase_client):
        """이메일 인증 메일 재발송 성공 테스트"""
        email = "test@example.com"

        user_usecase.resend_verification_email(email)

        # 호출 검증
        mock_supabase_client.auth.resend.assert_called_once()
        call_arg = mock_supabase_client.auth.resend.call_args.args[0]
        assert call_arg["type"] == "signup"
        assert call_arg["email"] == email

    def test_resend_verification_email_failure_raises(self, user_usecase, mock_supabase_client):
        """이메일 인증 메일 재발송 실패 시 예외가 전파되는 테스트"""
        mock_supabase_client.auth.resend.side_effect = Exception("Resend error")

        with pytest.raises(Exception, match="Resend error"):
            user_usecase.resend_verification_email("test@example.com")

    # ============= check_email_verification_from_auth =============

    def test_check_email_verification_verified(self, user_usecase):
        """Auth에서 이메일 인증 완료 상태 확인 테스트"""
        email = "test@example.com"
        auth_user = MagicMock()
        auth_user.email = email
        auth_user.email_confirmed_at = "2025-01-20T10:30:00Z"

        with patch("clients.get_supabase_admin_client") as mock_get_admin:
            mock_get_admin.return_value.auth.admin.list_users.return_value = [auth_user]

            result = user_usecase.check_email_verification_from_auth(email)

        assert result is True

    def test_check_email_verification_not_verified(self, user_usecase):
        """Auth에서 이메일 미인증 상태 확인 테스트"""
        email = "test@example.com"
        auth_user = MagicMock()
        auth_user.email = email
        auth_user.email_confirmed_at = None

        with patch("clients.get_supabase_admin_client") as mock_get_admin:
            mock_get_admin.return_value.auth.admin.list_users.return_value = [auth_user]

            result = user_usecase.check_email_verification_from_auth(email)

        assert result is False

    def test_check_email_verification_user_not_found(self, user_usecase):
        """Auth에서 사용자를 찾을 수 없는 경우 False 반환 테스트"""
        with patch("clients.get_supabase_admin_client") as mock_get_admin:
            mock_get_admin.return_value.auth.admin.list_users.return_value = []

            result = user_usecase.check_email_verification_from_auth("nonexistent@example.com")

        assert result is False

    def test_check_email_verification_exception_returns_false(self, user_usecase):
        """Auth 조회 중 예외 발생 시 False 반환 테스트"""
        with patch("clients.get_supabase_admin_client") as mock_get_admin:
            mock_get_admin.return_value.auth.admin.list_users.side_effect = Exception("Admin API error")

            result = user_usecase.check_email_verification_from_auth("test@example.com")

        assert result is False

    # ============= refresh_session =============

    def test_refresh_session_success(
        self, user_usecase, mock_user_repo, mock_supabase_client, mock_auth_response, sample_user_out
    ):
        """리프레시 세션 성공 테스트"""
        refresh_token = "test-refresh-token"
        mock_supabase_client.auth.refresh_session.return_value = mock_auth_response
        mock_user_repo.get_by_uuid.return_value = sample_user_out
        mock_user_repo.update_last_login.return_value = True

        result = user_usecase.refresh_session(refresh_token)

        # 호출 검증
        mock_supabase_client.auth.refresh_session.assert_called_once_with(refresh_token)
        mock_user_repo.get_by_uuid.assert_called_once_with(mock_auth_response.user.id)

        # 결과 검증 (새 토큰 정보 포함)
        assert isinstance(result, UserOut)
        assert result.access_token == "test-access-token"
        assert result.refresh_token == "test-refresh-token"

    def test_refresh_session_invalid_token_raises_custom(self, user_usecase, mock_supabase_client):
        """무효/이미 사용된 리프레시 토큰(AuthApiError) → InvalidRefreshTokenException (라우터에서 401)"""
        mock_supabase_client.auth.refresh_session.side_effect = AuthApiError(
            "Invalid Refresh Token: Already Used", 400, "refresh_token_already_used"
        )

        with pytest.raises(InvalidRefreshTokenException):
            user_usecase.refresh_session("already-used-token")

    def test_refresh_session_non_auth_error_propagates(self, user_usecase, mock_supabase_client):
        """AuthApiError가 아닌 오류(네트워크 등)는 그대로 전파 → 라우터에서 500"""
        mock_supabase_client.auth.refresh_session.side_effect = Exception("Network unreachable")

        with pytest.raises(Exception, match="Network unreachable"):
            user_usecase.refresh_session("some-token")
        # InvalidRefreshTokenException으로 잘못 변환되지 않아야 함
        try:
            user_usecase.refresh_session("some-token")
        except InvalidRefreshTokenException:
            pytest.fail("일반 오류가 InvalidRefreshTokenException으로 잘못 변환됨")
        except Exception:
            pass

    def test_refresh_session_db_user_not_found_returns_none(
        self, user_usecase, mock_user_repo, mock_supabase_client, mock_auth_response
    ):
        """리프레시 세션에서 DB 사용자가 없으면 None 반환 테스트"""
        mock_supabase_client.auth.refresh_session.return_value = mock_auth_response
        mock_user_repo.get_by_uuid.return_value = None

        result = user_usecase.refresh_session("test-refresh-token")

        assert result is None

    # ============= 스키마 검증 =============

    def test_user_create_password_validation(self):
        """UserCreate 비밀번호 검증 테스트 (최소 8자)"""
        # 유효한 비밀번호
        user_create = UserCreate(email="test@example.com", password="password123")
        assert user_create.password == "password123"

        # 8자 미만 비밀번호는 검증 실패
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="short")

    def test_user_create_timezone_validation(self):
        """UserCreate 타임존 검증 테스트 (허용 문자 패턴)"""
        valid_timezones = ["Asia/Seoul", "America/New_York", "Europe/London", "UTC"]
        # 패턴 검증이므로 허용되지 않는 문자(공백, 특수문자)가 있어야 실패
        invalid_timezones = ["Asia Seoul", "Asia/Seoul!"]

        for timezone in valid_timezones:
            user_create = UserCreate(email="test@example.com", timezone=timezone, language="ko")
            assert user_create.timezone == timezone

        for timezone in invalid_timezones:
            with pytest.raises(ValidationError):
                UserCreate(email="test@example.com", timezone=timezone, language="ko")

    def test_user_create_language_validation(self):
        """UserCreate 언어 코드 검증 테스트 (ISO 639-1)"""
        valid_languages = ["ko", "en", "ja", "zh"]
        invalid_languages = ["kor", "k1", "k"]

        for language in valid_languages:
            user_create = UserCreate(email="test@example.com", timezone="Asia/Seoul", language=language)
            assert user_create.language == language

        for language in invalid_languages:
            with pytest.raises(ValidationError):
                UserCreate(email="test@example.com", timezone="Asia/Seoul", language=language)
