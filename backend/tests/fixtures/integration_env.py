# tests/fixtures/integration_env.py
"""통합/E2E 테스트용 dev Supabase 환경 스캐폴딩.

설계:
- 통합 테스트는 mock이 아니라 **dev Supabase 프로젝트**를 상대로 실제 HTTP를 탄다.
- 옵트인: RUN_INTEGRATION=1 이고 루트에 .env.dev가 있으며 SUPABASE_URL이
  프로덕션(.env)과 다를 때만 수집된다. 아니면 전부 skip (unit 실행을 막지 않음).
- 인증: Supabase admin API로 이메일 인증이 완료된 테스트 유저를 만들고
  (확인 메일 발송 없음), 실제 로그인으로 JWT를 받아 API를 호출한다.
- 정리: 세션 종료 시 public.users 행(연쇄 삭제)과 auth 유저를 모두 제거한다.

사용: 각 conftest.py에서 `from tests.fixtures.integration_env import *`
"""
import os
import uuid as uuid_lib
from pathlib import Path

import pytest
from dotenv import dotenv_values, load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
TEST_PASSWORD = "integration-test-pw-1!"


def integration_disabled_reason() -> str | None:
    """통합 테스트를 돌릴 수 없는 이유. None이면 실행 가능."""
    if os.getenv("RUN_INTEGRATION") != "1":
        return "RUN_INTEGRATION=1 미설정 (dev Supabase 대상 통합 테스트는 옵트인)"
    if not (ROOT_DIR / ".env.dev").exists():
        return ".env.dev 없음 (dev Supabase 프로젝트 필요)"
    dev = dotenv_values(ROOT_DIR / ".env.dev").get("SUPABASE_URL")
    prod = dotenv_values(ROOT_DIR / ".env").get("SUPABASE_URL")
    if not dev or dev == prod:
        return ".env.dev의 SUPABASE_URL이 비었거나 프로덕션과 동일 (격리 안 됨)"
    return None


def pytest_collection_modifyitems(config, items):
    """게이트: 조건 미충족 시 이 디렉토리의 테스트 전체를 skip."""
    reason = integration_disabled_reason()
    if reason is None:
        return
    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        item.add_marker(skip_marker)


@pytest.fixture(scope="session", autouse=True)
def dev_env():
    """dev Supabase 환경변수 적용 (top-level conftest의 가짜 값을 덮어씀)."""
    if integration_disabled_reason():
        yield
        return
    load_dotenv(ROOT_DIR / ".env", override=True)
    load_dotenv(ROOT_DIR / ".env.dev", override=True)
    yield


@pytest.fixture(scope="session")
def auth_user(dev_env):
    """이메일 인증이 완료된 dev 테스트 유저 + JWT.

    반환: {"user_id", "auth_uuid", "email", "access_token", "refresh_token"}
    """
    from clients import get_supabase_admin_client, get_supabase_client
    from repo import get_db_client

    admin = get_supabase_admin_client()
    db = get_db_client()
    email = f"it-{uuid_lib.uuid4().hex[:10]}@porta.dev"

    # 1. 인증 완료 상태의 auth 유저 생성 (확인 메일 발송 없음)
    created = admin.auth.admin.create_user(
        {"email": email, "password": TEST_PASSWORD, "email_confirm": True}
    )
    auth_uuid = created.user.id

    # 2. public.users + portfolios 행 생성 (register_user 경로와 동일한 결과 상태)
    user_row = (
        db.table("users")
        .insert({"email": email, "uuid": auth_uuid, "email_verified": True, "language": "ko"})
        .execute()
        .data[0]
    )
    user_id = user_row["id"]
    db.table("portfolios").insert({"user_id": user_id, "cash": "10000.00"}).execute()

    # 3. 실제 로그인으로 JWT 획득
    anon = get_supabase_client()
    session = anon.auth.sign_in_with_password({"email": email, "password": TEST_PASSWORD})

    yield {
        "user_id": user_id,
        "auth_uuid": auth_uuid,
        "email": email,
        "access_token": session.session.access_token,
        "refresh_token": session.session.refresh_token,
    }

    # 4. 정리: users 행 삭제(포트폴리오/포지션/보고서 등 연쇄 삭제) + auth 유저 삭제
    try:
        db.table("users").delete().eq("id", user_id).execute()
    finally:
        try:
            admin.auth.admin.delete_user(auth_uuid)
        except Exception:
            pass


@pytest.fixture(scope="session")
def api_client(dev_env):
    """FastAPI TestClient (dev Supabase 대상)."""
    from fastapi.testclient import TestClient
    from app import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def auth_headers(auth_user):
    """인증된 요청용 Authorization 헤더."""
    return {"Authorization": f"Bearer {auth_user['access_token']}"}
