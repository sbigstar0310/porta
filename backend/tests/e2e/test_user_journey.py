# tests/e2e/test_user_journey.py
"""사용자 여정 End-to-End 테스트.

실제 dev Supabase 유저로 해피 패스 한 줄기를 순차 검증한다:
로그인 → 포트폴리오 조회 → 포지션 추가 → 포트폴리오에 반영 확인
→ 포지션 수정 → 포지션 삭제 → 포트폴리오 원상 복구.

주의:
- 회원가입은 실제 인증 메일을 발송하므로 세션 auth_user를 재사용한다.
- 에이전트 실행(POST /agent/run*)은 Celery/Redis가 필요하므로 호출하지 않는다.
"""
from decimal import Decimal

import pytest

from tests.fixtures.integration_env import TEST_PASSWORD

pytestmark = [pytest.mark.e2e]


class TestUserJourney:
    """로그인부터 포지션 정리까지의 해피 패스 여정 (단일 테스트, 순차 단계)."""

    def test_happy_path_journey(self, api_client, auth_user):
        """로그인 → 포트폴리오 → 포지션 추가/확인/수정/삭제 → 빈 포트폴리오."""
        position_id = None
        headers = None
        try:
            # ===== 1단계: 로그인 (실제 dev Supabase 인증) =====
            login = api_client.post(
                "/auth/login",
                data={"email": auth_user["email"], "password": TEST_PASSWORD},
            )
            assert login.status_code == 200, f"로그인 실패: {login.text}"
            login_data = login.json()
            assert login_data["email"] == auth_user["email"]
            assert login_data["access_token"]
            headers = {"Authorization": f"Bearer {login_data['access_token']}"}

            # ===== 2단계: 포트폴리오 조회 (시작 상태: 포지션 없음) =====
            portfolio = api_client.get("/portfolio", headers=headers)
            assert portfolio.status_code == 200
            portfolio_data = portfolio.json()
            assert portfolio_data["user_id"] == auth_user["user_id"]
            portfolio_id = portfolio_data["id"]
            assert portfolio_data["positions"] == []

            # ===== 3단계: 포지션 추가 (AAPL 매수 기록) =====
            created = api_client.post(
                "/position/",
                headers=headers,
                json={
                    "portfolio_id": portfolio_id,
                    "ticker": "AAPL",
                    "total_shares": 10,
                    "avg_buy_price": 150.00,
                },
            )
            assert created.status_code == 200, f"포지션 생성 실패: {created.text}"
            position_id = created.json()["id"]

            # ===== 4단계: 포트폴리오에 포지션 반영 확인 =====
            portfolio_with_position = api_client.get("/portfolio", headers=headers)
            assert portfolio_with_position.status_code == 200
            positions = portfolio_with_position.json()["positions"]
            assert len(positions) == 1
            aapl = positions[0]
            assert aapl["id"] == position_id
            assert aapl["ticker"] == "AAPL"
            assert Decimal(str(aapl["total_shares"])) == Decimal("10")
            # 실시간 계산 필드는 시세 조회 실패 시 None 허용 (키 존재만 보장)
            assert "current_price" in aapl
            assert "current_market_value" in aapl

            # ===== 5단계: 포지션 수정 (일부 매도 가정) =====
            patched = api_client.patch(
                f"/position/{position_id}",
                headers=headers,
                json={"total_shares": 4, "avg_buy_price": 155.50},
            )
            assert patched.status_code == 200
            patched_data = patched.json()
            assert Decimal(str(patched_data["total_shares"])) == Decimal("4")
            assert Decimal(str(patched_data["avg_buy_price"])) == Decimal("155.50")

            # ===== 6단계: 포지션 삭제 =====
            deleted = api_client.delete(f"/position/{position_id}", headers=headers)
            assert deleted.status_code == 200
            assert deleted.json()["success"] is True
            position_id = None  # 정리 완료

            # ===== 7단계: 포트폴리오가 다시 빈 상태인지 확인 =====
            final_portfolio = api_client.get("/portfolio", headers=headers)
            assert final_portfolio.status_code == 200
            assert final_portfolio.json()["positions"] == []
        finally:
            # 중간 실패 시에도 생성한 포지션은 반드시 정리
            if position_id is not None and headers is not None:
                api_client.delete(f"/position/{position_id}", headers=headers)
