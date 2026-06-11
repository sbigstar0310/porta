# tests/unit/test_graph/test_agent_pipeline.py
"""Root graph 구성 단위 테스트 (tier 기반 LLM 주입 구조).

전체 파이프라인 동작 검증은 backend/scripts/run_e2e.py(dev DB 대상)가 담당하고,
여기서는 그래프가 올바르게 조립되는지(노드/티어/클라이언트 공유)만 확인한다.
"""
import pytest
from unittest.mock import MagicMock, patch

from graph.root_graph import AGENT_TIERS, build_root_graph
from graph.llm_clients.openai_client import LLMTier

ALL_AGENTS = {"CRAWLER", "MOMO", "FUND", "REVIEWER", "RISK", "DECIDER", "REPORTER"}


def build_with_mocks(llm_factory=None):
    """Redis 없이 그래프를 빌드한다 (crawler 캐시 클라이언트 mock)."""
    factory = llm_factory or (lambda tier: MagicMock(name=f"llm-{tier}"))
    with patch("graph.agents.crawler.graph.get_cache_client", return_value=MagicMock()):
        return build_root_graph(llm_factory=factory)


@pytest.mark.unit
@pytest.mark.agent
class TestRootGraphAssembly:
    def test_graph_builds_and_contains_all_agent_nodes(self):
        app = build_with_mocks()
        node_names = set(app.get_graph().nodes.keys())
        assert ALL_AGENTS <= node_names

    def test_every_agent_has_tier_assignment(self):
        assert set(AGENT_TIERS.keys()) == ALL_AGENTS
        assert all(isinstance(tier, LLMTier) for tier in AGENT_TIERS.values())

    def test_llm_clients_are_shared_per_tier(self):
        created_tiers = []

        def factory(tier):
            created_tiers.append(tier)
            return MagicMock(name=f"llm-{tier}")

        build_with_mocks(llm_factory=factory)

        # 사용된 티어 종류만큼만 클라이언트가 생성된다 (티어당 1회, 에이전트당 1회가 아님)
        used_tiers = set(AGENT_TIERS.values())
        assert len(created_tiers) == len(used_tiers)
        assert set(created_tiers) == used_tiers
