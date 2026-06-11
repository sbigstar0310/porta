# tests/unit/test_clients/test_supabase_client.py
"""
SupabaseClient / SupabaseAdminClient 단위 테스트

- anon 키(SUPABASE_KEY) 기반 SupabaseClient와
  service_role 키(SUPABASE_SERVICE_ROLE_KEY) 기반 SupabaseAdminClient 분리 구조 검증
- create_client는 mock 처리 (실제 네트워크 없음)
"""
import pytest
from unittest.mock import patch, MagicMock

from clients.supabase_client import SupabaseClient, SupabaseAdminClient


TEST_URL = "https://test.supabase.co"
ANON_KEY = "test-anon-key"
SERVICE_KEY = "test-service-role-key"


@pytest.fixture
def env(monkeypatch):
    """테스트 기본 환경변수 설정 (conftest 전역 설정과 무관하게 격리)"""
    monkeypatch.setenv("SUPABASE_URL", TEST_URL)
    monkeypatch.setenv("SUPABASE_KEY", ANON_KEY)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", SERVICE_KEY)
    return monkeypatch


@pytest.mark.unit
class TestSupabaseClient:
    """anon 키 기반 클라이언트 (auth 작업용) 테스트"""

    @patch("clients.supabase_client.create_client")
    def test_creates_client_with_anon_key(self, mock_create_client, env):
        """SUPABASE_URL + SUPABASE_KEY(anon)로 클라이언트가 생성되는지 테스트"""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = SupabaseClient()

        mock_create_client.assert_called_once_with(TEST_URL, ANON_KEY)
        assert client.get_client() is mock_client

    @patch("clients.supabase_client.create_client")
    def test_does_not_use_service_role_key(self, mock_create_client, env):
        """일반 클라이언트는 service_role 키를 사용하지 않는지 테스트"""
        SupabaseClient()

        (url, key) = mock_create_client.call_args.args
        assert key == ANON_KEY
        assert key != SERVICE_KEY

    def test_missing_url_raises(self, env):
        """SUPABASE_URL 누락 시 ValueError 테스트"""
        env.delenv("SUPABASE_URL")

        with pytest.raises(ValueError, match="Missing Supabase config"):
            SupabaseClient()

    def test_missing_key_raises(self, env):
        """SUPABASE_KEY 누락 시 ValueError 테스트"""
        env.delenv("SUPABASE_KEY")

        with pytest.raises(ValueError, match="Missing Supabase config"):
            SupabaseClient()

    @patch("clients.supabase_client.create_client")
    def test_create_client_error_propagates(self, mock_create_client, env):
        """create_client 실패 시 예외가 전파되는지 테스트"""
        mock_create_client.side_effect = ConnectionError("Failed to connect")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            SupabaseClient()


@pytest.mark.unit
class TestSupabaseAdminClient:
    """service_role 키 기반 admin 클라이언트 (데이터 레이어/RLS 우회) 테스트"""

    @patch("clients.supabase_client.create_client")
    def test_creates_client_with_service_role_key(self, mock_create_client, env):
        """SUPABASE_SERVICE_ROLE_KEY로 클라이언트가 생성되는지 테스트"""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = SupabaseAdminClient()

        mock_create_client.assert_called_once_with(TEST_URL, SERVICE_KEY)
        assert client.get_client() is mock_client

    @patch("clients.supabase_client.create_client")
    def test_falls_back_to_anon_key_when_service_key_missing(self, mock_create_client, env):
        """SUPABASE_SERVICE_ROLE_KEY 미설정 시 SUPABASE_KEY로 폴백하는지 테스트"""
        env.delenv("SUPABASE_SERVICE_ROLE_KEY")

        SupabaseAdminClient()

        mock_create_client.assert_called_once_with(TEST_URL, ANON_KEY)

    @patch("clients.supabase_client.create_client")
    def test_empty_service_key_falls_back_to_anon_key(self, mock_create_client, env):
        """SUPABASE_SERVICE_ROLE_KEY가 빈 문자열이어도 SUPABASE_KEY로 폴백하는지 테스트"""
        env.setenv("SUPABASE_SERVICE_ROLE_KEY", "")

        SupabaseAdminClient()

        mock_create_client.assert_called_once_with(TEST_URL, ANON_KEY)

    def test_missing_url_raises(self, env):
        """SUPABASE_URL 누락 시 ValueError 테스트"""
        env.delenv("SUPABASE_URL")

        with pytest.raises(ValueError, match="Missing Supabase admin config"):
            SupabaseAdminClient()

    def test_missing_both_keys_raises(self, env):
        """service_role 키와 anon 키 모두 누락 시 ValueError 테스트"""
        env.delenv("SUPABASE_SERVICE_ROLE_KEY")
        env.delenv("SUPABASE_KEY")

        with pytest.raises(ValueError, match="Missing Supabase admin config"):
            SupabaseAdminClient()


@pytest.mark.unit
class TestClientFactories:
    """clients/__init__.py 팩토리 함수 테스트"""

    @patch("clients.supabase_client.create_client")
    def test_get_supabase_client_returns_raw_client(self, mock_create_client, env):
        """get_supabase_client가 anon 키 기반 raw Client를 반환하는지 테스트"""
        from clients import get_supabase_client

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = get_supabase_client()

        mock_create_client.assert_called_once_with(TEST_URL, ANON_KEY)
        assert client is mock_client

    @patch("clients.supabase_client.create_client")
    def test_get_supabase_admin_client_returns_raw_client(self, mock_create_client, env):
        """get_supabase_admin_client가 service_role 키 기반 raw Client를 반환하는지 테스트"""
        from clients import get_supabase_admin_client

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = get_supabase_admin_client()

        mock_create_client.assert_called_once_with(TEST_URL, SERVICE_KEY)
        assert client is mock_client
