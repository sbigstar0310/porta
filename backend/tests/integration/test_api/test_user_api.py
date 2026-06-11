# tests/integration/test_api/test_user_api.py
"""User / Auth API 통합 테스트.

실제 dev Supabase 유저(auth_user 픽스처)로 사용자 조회와 인증 플로우를 검증한다.
- 회원가입(POST /users)과 인증 메일 재발송은 실제 메일을 발송하므로 테스트하지 않는다.
"""
import pytest

from tests.fixtures.integration_env import TEST_PASSWORD

pytestmark = [pytest.mark.integration, pytest.mark.api]

# 존재할 수 없는 충분히 큰 user_id
NONEXISTENT_USER_ID = 2_147_000_000


class TestUserAPI:
    """GET /users/{user_id}"""

    def test_get_own_user(self, api_client, auth_headers, auth_user):
        """자기 자신 조회: 200 + 이메일 일치."""
        response = api_client.get(f"/users/{auth_user['user_id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auth_user["user_id"]
        assert data["email"] == auth_user["email"]
        assert "timezone" in data
        assert "language" in data

    def test_get_own_user_email_verified_reflects_db(self, api_client, auth_headers, auth_user):
        """인증 완료 유저 조회 시 email_verified=True를 반환한다 (get_by_id 매핑 버그 수정 확인)."""
        response = api_client.get(f"/users/{auth_user['user_id']}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["email_verified"] is True

    def test_get_other_user_forbidden(self, api_client, auth_headers):
        """타인(또는 존재하지 않는) user_id 조회: 403 — 본인 프로필만 조회 가능."""
        response = api_client.get(f"/users/{NONEXISTENT_USER_ID}", headers=auth_headers)

        assert response.status_code == 403

    def test_protected_endpoint_without_token(self, api_client, auth_user):
        """토큰 없이 보호된 엔드포인트 접근: 401/403 (유저 조회·포트폴리오 모두 보호됨)."""
        assert api_client.get(f"/users/{auth_user['user_id']}").status_code in (401, 403)
        assert api_client.get("/portfolio").status_code in (401, 403)

    def test_protected_endpoint_with_invalid_token(self, api_client):
        """위조/무효 토큰으로 접근: 401/403."""
        response = api_client.get(
            "/portfolio", headers={"Authorization": "Bearer this-is-not-a-valid-jwt"}
        )

        assert response.status_code in (401, 403)


class TestAuthAPI:
    """POST /auth/login, /auth/refresh, GET /auth/email-verification-status/{email}"""

    def test_login_returns_tokens(self, api_client, auth_user):
        """실제 dev 유저로 로그인: 200 + 액세스/리프레시 토큰 포함."""
        response = api_client.post(
            "/auth/login",
            data={"email": auth_user["email"], "password": TEST_PASSWORD},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auth_user["user_id"]
        assert data["email"] == auth_user["email"]
        assert data["access_token"]
        assert data["refresh_token"]

    def test_login_with_wrong_password_fails(self, api_client, auth_user):
        """잘못된 비밀번호 로그인: 4xx/5xx (성공해서는 안 됨)."""
        response = api_client.post(
            "/auth/login",
            data={"email": auth_user["email"], "password": "definitely-wrong-pw-1!"},
        )

        assert response.status_code >= 400

    def test_refresh_token_rotates_session(self, api_client, auth_user):
        """리프레시 토큰으로 세션 갱신: 새 토큰 발급.

        세션 픽스처의 refresh_token을 소모하지 않도록, 먼저 로그인으로
        새 세션(토큰 패밀리)을 만들고 그 refresh_token을 갱신한다.
        """
        login = api_client.post(
            "/auth/login",
            data={"email": auth_user["email"], "password": TEST_PASSWORD},
        )
        assert login.status_code == 200
        fresh_refresh_token = login.json()["refresh_token"]

        response = api_client.post("/auth/refresh", data={"refresh_token": fresh_refresh_token})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == auth_user["email"]
        assert data["access_token"]
        assert data["refresh_token"]

    def test_email_verification_status(self, api_client, auth_user):
        """이메일 인증 상태 확인 (토큰 불필요): 인증 완료 유저는 True."""
        response = api_client.get(f"/auth/email-verification-status/{auth_user['email']}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == auth_user["email"]
        assert data["email_verified"] is True
        assert "timestamp" in data
