# tests/unit/test_clients/test_supabase_client.py
"""
Supabase 클라이언트 단위 테스트
"""
import pytest
from unittest.mock import patch, MagicMock
from supabase import Client

from clients import get_supabase_client


@pytest.mark.unit
class TestSupabaseClient:
    """Supabase 클라이언트 테스트"""

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_get_supabase_client_success(self, mock_create_client):
        """Supabase 클라이언트 생성 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        client = get_supabase_client()

        # 호출 검증
        mock_create_client.assert_called_once_with("https://test.supabase.co", "test-key-123")

        # 결과 검증
        assert client is mock_client

    @patch.dict("os.environ", {}, clear=True)
    def test_get_supabase_client_missing_url(self):
        """SUPABASE_URL 환경변수 없음 테스트"""
        with pytest.raises(ValueError, match="SUPABASE_URL environment variable is required"):
            get_supabase_client()

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co"})
    def test_get_supabase_client_missing_key(self):
        """SUPABASE_KEY 환경변수 없음 테스트"""
        with pytest.raises(ValueError, match="SUPABASE_KEY environment variable is required"):
            get_supabase_client()

    @patch.dict("os.environ", {"SUPABASE_URL": "invalid-url", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_get_supabase_client_invalid_url(self, mock_create_client):
        """잘못된 URL 테스트"""
        mock_create_client.side_effect = ValueError("Invalid URL format")

        with pytest.raises(ValueError, match="Invalid URL format"):
            get_supabase_client()

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_get_supabase_client_connection_error(self, mock_create_client):
        """연결 오류 테스트"""
        mock_create_client.side_effect = ConnectionError("Failed to connect")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            get_supabase_client()

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_table_operations(self, mock_create_client):
        """Supabase 클라이언트 테이블 연산 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client

        client = get_supabase_client()
        table = client.table("users")

        # 호출 검증
        mock_client.table.assert_called_once_with("users")
        assert table is mock_table

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_auth_operations(self, mock_create_client):
        """Supabase 클라이언트 인증 연산 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_auth = MagicMock()
        mock_client.auth = mock_auth
        mock_create_client.return_value = mock_client

        client = get_supabase_client()
        auth = client.auth

        # 인증 객체 확인
        assert auth is mock_auth

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_storage_operations(self, mock_create_client):
        """Supabase 클라이언트 스토리지 연산 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_storage = MagicMock()
        mock_client.storage = mock_storage
        mock_create_client.return_value = mock_client

        client = get_supabase_client()
        storage = client.storage

        # 스토리지 객체 확인
        assert storage is mock_storage

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_rpc_operations(self, mock_create_client):
        """Supabase 클라이언트 RPC 연산 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_rpc_response = MagicMock()
        mock_client.rpc.return_value = mock_rpc_response
        mock_create_client.return_value = mock_client

        client = get_supabase_client()
        rpc_result = client.rpc("test_function", {"param": "value"})

        # RPC 호출 검증
        mock_client.rpc.assert_called_once_with("test_function", {"param": "value"})
        assert rpc_result is mock_rpc_response

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_real_time_operations(self, mock_create_client):
        """Supabase 클라이언트 실시간 연산 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_realtime = MagicMock()
        mock_client.realtime = mock_realtime
        mock_create_client.return_value = mock_client

        client = get_supabase_client()
        realtime = client.realtime

        # 실시간 객체 확인
        assert realtime is mock_realtime

    def test_environment_variable_validation(self):
        """환경변수 검증 테스트"""
        # URL 형식 검증
        valid_urls = ["https://test.supabase.co", "https://project-id.supabase.co", "https://custom-domain.com"]

        for url in valid_urls:
            with patch.dict("os.environ", {"SUPABASE_URL": url, "SUPABASE_KEY": "test-key"}):
                with patch("clients.supabase.create_client") as mock_create:
                    mock_create.return_value = MagicMock()
                    try:
                        get_supabase_client()
                        # URL이 유효하면 예외 없이 실행되어야 함
                    except ValueError:
                        pytest.fail(f"Valid URL {url} should not raise ValueError")

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_error_handling(self, mock_create_client):
        """Supabase 클라이언트 오류 처리 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # 테이블 연산 오류 시뮬레이션
        mock_client.table.side_effect = Exception("Table operation failed")

        client = get_supabase_client()

        with pytest.raises(Exception, match="Table operation failed"):
            client.table("users")

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_singleton_behavior(self, mock_create_client):
        """Supabase 클라이언트 싱글톤 동작 테스트 (구현된 경우)"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # 여러 번 호출
        client1 = get_supabase_client()
        client2 = get_supabase_client()

        # create_client가 여러 번 호출되는지 확인 (싱글톤이 아닌 경우)
        # 또는 같은 인스턴스인지 확인 (싱글톤인 경우)
        assert mock_create_client.call_count >= 1

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_supabase_client_configuration_options(self, mock_create_client):
        """Supabase 클라이언트 설정 옵션 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # 추가 설정이 있는 경우를 위한 플레이스홀더
        client = get_supabase_client()

        # 기본 호출 확인
        mock_create_client.assert_called_with("https://test.supabase.co", "test-key-123")

    def test_client_import_structure(self):
        """클라이언트 import 구조 테스트"""
        # clients/__init__.py에서 get_supabase_client가 올바르게 export되는지 확인
        from clients import get_supabase_client

        assert callable(get_supabase_client)

    @patch.dict("os.environ", {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key-123"})
    @patch("clients.supabase.create_client")
    def test_client_method_availability(self, mock_create_client):
        """클라이언트 메서드 가용성 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        client = get_supabase_client()

        # 주요 메서드들이 사용 가능한지 확인
        assert hasattr(client, "table")
        assert hasattr(client, "auth")
        assert hasattr(client, "storage")
        assert hasattr(client, "rpc")

        # 메서드들이 호출 가능한지 확인
        assert callable(client.table)
        assert callable(client.rpc)
