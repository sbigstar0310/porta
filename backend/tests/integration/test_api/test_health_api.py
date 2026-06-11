# tests/integration/test_api/test_health_api.py
"""Health API 통합 테스트.

dev Supabase 프로젝트를 상대로 실제 헬스체크 엔드포인트를 호출한다.
(인증 불필요 — /health/db는 실제 dev DB 연결을 확인한다.)
"""
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.api]


class TestHealthAPI:
    """GET /health, GET /health/db"""

    def test_health_returns_healthy(self, api_client):
        """기본 헬스체크: 200 + status=healthy + 안내 메시지."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data and data["message"]

    def test_health_db_connects_to_dev_supabase(self, api_client):
        """DB 헬스체크: 실제 dev Supabase에 연결되어 healthy를 반환해야 한다."""
        response = api_client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connected"] is True
        assert "message" in data
