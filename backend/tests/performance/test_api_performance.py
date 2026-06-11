# tests/performance/test_api_performance.py
"""API 성능 새너티 테스트 (가벼운 수준만).

실제 dev Supabase(무료 티어)를 때리므로 요청 수는 최소(N=10)로 유지하고,
지연 한계는 네트워크 변동을 감안해 느슨하게(3초) 잡는다.
"""
import math
import time

import pytest

pytestmark = [pytest.mark.performance, pytest.mark.slow]

N_REQUESTS = 10
P95_LIMIT_SECONDS = 3.0


class TestAPIPerformance:
    """GET /portfolio 순차 호출 지연 새너티."""

    def test_get_portfolio_p95_latency(self, api_client, auth_headers):
        """포트폴리오 조회 10회 순차 호출: 전부 200, p95 < 3초."""
        latencies: list[float] = []

        for _ in range(N_REQUESTS):
            start = time.perf_counter()
            response = api_client.get("/portfolio", headers=auth_headers)
            latencies.append(time.perf_counter() - start)
            assert response.status_code == 200

        latencies.sort()
        p95_index = max(0, math.ceil(0.95 * N_REQUESTS) - 1)
        p95 = latencies[p95_index]

        assert p95 < P95_LIMIT_SECONDS, (
            f"p95 지연 {p95:.3f}s가 한계 {P95_LIMIT_SECONDS}s를 초과 "
            f"(전체: {[f'{lat:.3f}' for lat in latencies]})"
        )
