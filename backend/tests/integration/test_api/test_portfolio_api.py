# tests/integration/test_api/test_portfolio_api.py
"""Portfolio / Position API 통합 테스트.

실제 dev Supabase의 포트폴리오(현금 $10,000, 포지션 없음)를 상대로
조회/수정과 포지션 CRUD 풀 사이클을 검증한다. 생성한 행은 테스트 내에서 정리한다.
"""
from decimal import Decimal

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.api]


class TestPortfolioAPI:
    """GET /portfolio, PATCH /portfolio"""

    def test_get_portfolio(self, api_client, auth_headers, auth_user):
        """포트폴리오 조회: 200 + 소유자/통화/현금/포지션 목록 확인."""
        response = api_client.get("/portfolio", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == auth_user["user_id"]
        assert data["base_currency"] == "USD"
        assert "cash" in data
        assert Decimal(str(data["cash"])) >= 0
        assert isinstance(data["positions"], list)

    def test_patch_portfolio_cash_and_restore(self, api_client, auth_headers):
        """현금 수정 후 재조회로 반영 확인, 마지막에 원래 값으로 복원."""
        original = api_client.get("/portfolio", headers=auth_headers)
        assert original.status_code == 200
        original_cash = str(original.json()["cash"])

        new_cash = "5432.10"
        try:
            patched = api_client.patch("/portfolio", headers=auth_headers, json={"cash": new_cash})
            assert patched.status_code == 200
            assert Decimal(str(patched.json()["cash"])) == Decimal(new_cash)

            # 재조회로 영속 반영 확인
            refetched = api_client.get("/portfolio", headers=auth_headers)
            assert refetched.status_code == 200
            assert Decimal(str(refetched.json()["cash"])) == Decimal(new_cash)
        finally:
            # 복원 (다른 테스트의 전제 조건 유지)
            restored = api_client.patch(
                "/portfolio", headers=auth_headers, json={"cash": original_cash}
            )
            assert restored.status_code == 200
            assert Decimal(str(restored.json()["cash"])) == Decimal(original_cash)

    def test_get_portfolio_without_token(self, api_client):
        """토큰 없이 조회: 401/403."""
        response = api_client.get("/portfolio")

        assert response.status_code in (401, 403)

    def test_patch_portfolio_with_invalid_token(self, api_client):
        """무효 토큰으로 수정 시도: 401/403 (데이터 변경 없어야 함)."""
        response = api_client.patch(
            "/portfolio",
            headers={"Authorization": "Bearer invalid-token"},
            json={"cash": "1.00"},
        )

        assert response.status_code in (401, 403)


class TestPositionAPI:
    """POST/GET/PATCH/DELETE /position — 생성→조회→수정→삭제 풀 사이클."""

    def test_position_full_lifecycle(self, api_client, auth_headers, auth_user):
        """AAPL 포지션 생성→조회→수정→삭제, 종료 시 포트폴리오는 다시 빈 상태."""
        portfolio = api_client.get("/portfolio", headers=auth_headers)
        assert portfolio.status_code == 200
        portfolio_id = portfolio.json()["id"]

        position_id = None
        try:
            # 1. 생성
            created = api_client.post(
                "/position/",
                headers=auth_headers,
                json={
                    "portfolio_id": portfolio_id,
                    "ticker": "AAPL",
                    "total_shares": 10,
                    "avg_buy_price": 150.25,
                },
            )
            assert created.status_code == 200
            created_data = created.json()
            position_id = created_data["id"]
            assert created_data["portfolio_id"] == portfolio_id
            assert created_data["ticker"] == "AAPL"
            assert Decimal(str(created_data["total_shares"])) == Decimal("10")
            assert Decimal(str(created_data["avg_buy_price"])) == Decimal("150.25")

            # 2. 단건 조회 (실시간 가격 필드는 시세 조회 실패 시 None 허용)
            fetched = api_client.get(f"/position/{position_id}", headers=auth_headers)
            assert fetched.status_code == 200
            fetched_data = fetched.json()
            assert fetched_data["id"] == position_id
            assert fetched_data["ticker"] == "AAPL"
            assert "current_price" in fetched_data  # 값은 None일 수 있음

            # 3. 수정
            patched = api_client.patch(
                f"/position/{position_id}",
                headers=auth_headers,
                json={"total_shares": 5, "avg_buy_price": 160.00},
            )
            assert patched.status_code == 200
            patched_data = patched.json()
            assert Decimal(str(patched_data["total_shares"])) == Decimal("5")
            assert Decimal(str(patched_data["avg_buy_price"])) == Decimal("160")

            # 4. 포트폴리오에 반영 확인
            portfolio_after = api_client.get("/portfolio", headers=auth_headers)
            assert portfolio_after.status_code == 200
            tickers = [p["ticker"] for p in portfolio_after.json()["positions"]]
            assert "AAPL" in tickers

            # 5. 삭제
            deleted = api_client.delete(f"/position/{position_id}", headers=auth_headers)
            assert deleted.status_code == 200
            assert deleted.json()["success"] is True
            position_id = None  # 정리 완료 표시

            # 6. 포트폴리오가 다시 빈 상태인지 확인
            portfolio_final = api_client.get("/portfolio", headers=auth_headers)
            assert portfolio_final.status_code == 200
            assert all(p["ticker"] != "AAPL" for p in portfolio_final.json()["positions"])
        finally:
            # 어서션 실패 시에도 생성한 포지션은 반드시 정리
            if position_id is not None:
                api_client.delete(f"/position/{position_id}", headers=auth_headers)

    def test_position_endpoints_require_auth(self, api_client):
        """포지션 엔드포인트는 토큰 없이는 401/403."""
        assert api_client.get("/position/1").status_code in (401, 403)
        assert (
            api_client.post(
                "/position/",
                json={
                    "portfolio_id": 1,
                    "ticker": "AAPL",
                    "total_shares": 1,
                    "avg_buy_price": 1,
                },
            ).status_code
            in (401, 403)
        )
        assert api_client.delete("/position/1").status_code in (401, 403)
