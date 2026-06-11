# tests/unit/test_data/test_db.py
"""
Database 클래스 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from supabase import Client

from data.db import Database


@pytest.mark.unit
class TestDatabase:
    """Database 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전에 Database 싱글톤 초기화"""
        Database._instance = None
        Database._client = None
        Database._initialized = False

    def teardown_method(self):
        """각 테스트 후에 Database 싱글톤 정리"""
        Database._instance = None
        Database._client = None
        Database._initialized = False

    def test_database_singleton_pattern(self):
        """Database 싱글톤 패턴 테스트"""
        # 첫 번째 인스턴스 생성
        db1 = Database()

        # 두 번째 인스턴스 생성
        db2 = Database()

        # 같은 인스턴스인지 확인
        assert db1 is db2
        assert Database._instance is db1

    @pytest.mark.asyncio
    @patch("data.db.get_supabase_client")
    async def test_database_initialize_success(self, mock_get_client):
        """Database 초기화 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # 초기화 전 상태 확인
        assert Database._client is None

        # 초기화 실행
        db = await Database.initialize()

        # 초기화 후 상태 확인
        assert isinstance(db, Database)
        assert db.client is mock_client
        mock_get_client.assert_called_once()

    @pytest.mark.asyncio
    @patch("data.db.get_supabase_client")
    async def test_database_initialize_already_initialized(self, mock_get_client):
        """이미 초기화된 경우 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # 첫 번째 초기화
        db1 = await Database.initialize()

        # 두 번째 초기화 시도
        db2 = await Database.initialize()

        # 같은 싱글톤 인스턴스를 반환하고 클라이언트가 유효해야 함
        assert db1 is db2
        assert db2.client is mock_client

    @pytest.mark.asyncio
    @patch("data.db.get_supabase_client")
    async def test_database_initialize_failure(self, mock_get_client):
        """Database 초기화 실패 테스트"""
        mock_get_client.side_effect = Exception("Connection failed")

        # 초기화 실행 시 예외 발생 확인
        with pytest.raises(Exception, match="Connection failed"):
            await Database.initialize()

        # 초기화 실패 후 클라이언트는 설정되지 않음
        assert Database._client is None

    def test_database_client_property_success(self):
        """client 프로퍼티 조회 성공 테스트"""
        mock_client = MagicMock(spec=Client)

        # Database 인스턴스 생성 및 클라이언트 설정
        Database._client = mock_client

        db = Database()

        assert db.client is mock_client

    def test_database_client_property_not_initialized(self):
        """초기화되지 않은 상태에서 client 프로퍼티 조회 테스트"""
        db = Database()

        with pytest.raises(RuntimeError, match="초기화되지 않았습니다"):
            _ = db.client

    @pytest.mark.asyncio
    async def test_database_health_check_success(self):
        """헬스체크 성공 테스트"""
        mock_client = MagicMock(spec=Client)

        # Mock health check response
        mock_response = MagicMock()
        mock_response.count = 1
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response

        Database._client = mock_client

        db = Database()
        result = await db.health_check()

        # 결과 검증
        assert result["status"] == "healthy"
        assert result["connected"] is True
        assert "message" in result
        mock_client.table.assert_called_once_with("users")

    @pytest.mark.asyncio
    async def test_database_health_check_failure(self):
        """헬스체크 실패 테스트"""
        mock_client = MagicMock(spec=Client)

        # Mock health check error
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "DB Error"
        )

        Database._client = mock_client

        db = Database()
        result = await db.health_check()

        # 결과 검증
        assert result["status"] == "unhealthy"
        assert result["connected"] is False
        assert "DB Error" in result["error"]

    @pytest.mark.asyncio
    async def test_database_health_check_not_initialized(self):
        """초기화되지 않은 상태에서 헬스체크 테스트"""
        db = Database()

        result = await db.health_check()

        # 클라이언트 미초기화 RuntimeError가 unhealthy 결과로 변환됨
        assert result["status"] == "unhealthy"
        assert result["connected"] is False
        assert "초기화되지 않았습니다" in result["error"]

    @pytest.mark.asyncio
    async def test_database_close_with_client(self):
        """클라이언트가 설정된 상태에서 연결 종료 테스트"""
        mock_client = MagicMock(spec=Client)
        Database._client = mock_client

        db = Database()

        # 예외 발생 없이 정상적으로 실행되어야 함
        await db.close()

    @pytest.mark.asyncio
    async def test_database_close_not_initialized(self):
        """초기화되지 않은 상태에서 연결 종료 테스트"""
        db = Database()

        # 예외 발생하지 않고 정상적으로 실행되어야 함
        await db.close()

        assert Database._client is None

    def test_database_multiple_instances_same_client(self):
        """여러 Database 인스턴스가 같은 클라이언트를 공유하는지 테스트"""
        mock_client = MagicMock(spec=Client)
        Database._client = mock_client

        db1 = Database()
        db2 = Database()

        # 같은 클라이언트를 공유하는지 확인
        assert db1.client is db2.client
        assert db1.client is mock_client
