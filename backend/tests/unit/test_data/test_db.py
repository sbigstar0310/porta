# tests/unit/test_data/test_db.py
"""
Database 클래스 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
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

    @patch("data.db.get_supabase_client")
    def test_database_singleton_pattern(self, mock_get_client):
        """Database 싱글톤 패턴 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # 첫 번째 인스턴스 생성
        db1 = Database()

        # 두 번째 인스턴스 생성
        db2 = Database()

        # 같은 인스턴스인지 확인
        assert db1 is db2
        assert Database._instance is db1

    @patch("data.db.get_supabase_client")
    async def test_database_initialize_success(self, mock_get_client):
        """Database 초기화 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # 초기화 전 상태 확인
        assert Database._initialized is False
        assert Database._client is None

        # 초기화 실행
        await Database.initialize()

        # 초기화 후 상태 확인
        assert Database._initialized is True
        assert Database._client is mock_client
        mock_get_client.assert_called_once()

    @patch("data.db.get_supabase_client")
    async def test_database_initialize_already_initialized(self, mock_get_client):
        """이미 초기화된 경우 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # 첫 번째 초기화
        await Database.initialize()

        # 두 번째 초기화 시도
        await Database.initialize()

        # get_supabase_client가 한 번만 호출되었는지 확인
        mock_get_client.assert_called_once()

    @patch("data.db.get_supabase_client")
    async def test_database_initialize_failure(self, mock_get_client):
        """Database 초기화 실패 테스트"""
        mock_get_client.side_effect = Exception("Connection failed")

        # 초기화 실행 시 예외 발생 확인
        with pytest.raises(Exception, match="Connection failed"):
            await Database.initialize()

        # 초기화 실패 후 상태 확인
        assert Database._initialized is False
        assert Database._client is None

    @patch("data.db.get_supabase_client")
    def test_database_get_client_success(self, mock_get_client):
        """클라이언트 조회 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Database 인스턴스 생성 및 클라이언트 설정
        Database._client = mock_client
        Database._initialized = True

        db = Database()
        client = db.get_client()

        assert client is mock_client

    def test_database_get_client_not_initialized(self):
        """초기화되지 않은 상태에서 클라이언트 조회 테스트"""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not initialized"):
            db.get_client()

    @patch("data.db.get_supabase_client")
    async def test_database_health_check_success(self, mock_get_client):
        """헬스체크 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock health check response
        mock_response = MagicMock()
        mock_response.data = [{"status": "healthy"}]
        mock_client.table().select().limit().execute.return_value = mock_response

        Database._client = mock_client
        Database._initialized = True

        db = Database()
        result = await db.health_check()

        # 결과 검증
        assert result["status"] == "healthy"
        assert result["connected"] is True
        assert "timestamp" in result

    @patch("data.db.get_supabase_client")
    async def test_database_health_check_failure(self, mock_get_client):
        """헬스체크 실패 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock health check error
        mock_client.table().select().limit().execute.side_effect = Exception("DB Error")

        Database._client = mock_client
        Database._initialized = True

        db = Database()
        result = await db.health_check()

        # 결과 검증
        assert result["status"] == "error"
        assert result["connected"] is False
        assert "error" in result

    @patch("data.db.get_supabase_client")
    async def test_database_health_check_not_initialized(self, mock_get_client):
        """초기화되지 않은 상태에서 헬스체크 테스트"""
        db = Database()

        result = await db.health_check()

        # 결과 검증
        assert result["status"] == "error"
        assert result["connected"] is False
        assert "Database not initialized" in result["error"]

    @patch("data.db.get_supabase_client")
    async def test_database_close_success(self, mock_get_client):
        """Database 연결 종료 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        Database._client = mock_client
        Database._initialized = True

        db = Database()
        await db.close()

        # 종료 후 상태 확인
        assert Database._client is None
        assert Database._initialized is False

    async def test_database_close_not_initialized(self):
        """초기화되지 않은 상태에서 연결 종료 테스트"""
        db = Database()

        # 예외 발생하지 않고 정상적으로 실행되어야 함
        await db.close()

        assert Database._client is None
        assert Database._initialized is False

    @patch("data.db.get_supabase_client")
    def test_database_table_access(self, mock_get_client):
        """테이블 접근 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client

        Database._client = mock_client
        Database._initialized = True

        db = Database()
        table = db.table("users")

        # 호출 검증
        mock_client.table.assert_called_once_with("users")
        assert table is mock_table

    def test_database_table_access_not_initialized(self):
        """초기화되지 않은 상태에서 테이블 접근 테스트"""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not initialized"):
            db.table("users")

    @patch("data.db.get_supabase_client")
    async def test_database_execute_query_success(self, mock_get_client):
        """쿼리 실행 성공 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock query response
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "name": "test"}]
        mock_client.table().select().execute.return_value = mock_response

        Database._client = mock_client
        Database._initialized = True

        db = Database()
        result = await db.execute_query("SELECT * FROM users")

        # 결과 검증
        assert result.data == [{"id": 1, "name": "test"}]

    @patch("data.db.get_supabase_client")
    async def test_database_execute_query_failure(self, mock_get_client):
        """쿼리 실행 실패 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Mock query error
        mock_client.table().select().execute.side_effect = Exception("Query failed")

        Database._client = mock_client
        Database._initialized = True

        db = Database()

        with pytest.raises(Exception, match="Query failed"):
            await db.execute_query("SELECT * FROM users")

    def test_database_execute_query_not_initialized(self):
        """초기화되지 않은 상태에서 쿼리 실행 테스트"""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not initialized"):
            asyncio.run(db.execute_query("SELECT * FROM users"))

    @patch("data.db.get_supabase_client")
    def test_database_connection_info(self, mock_get_client):
        """연결 정보 조회 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        Database._client = mock_client
        Database._initialized = True

        db = Database()
        info = db.get_connection_info()

        # 연결 정보 검증
        assert info["initialized"] is True
        assert info["client_type"] == type(mock_client).__name__
        assert "connection_time" in info

    def test_database_connection_info_not_initialized(self):
        """초기화되지 않은 상태에서 연결 정보 조회 테스트"""
        db = Database()
        info = db.get_connection_info()

        # 연결 정보 검증
        assert info["initialized"] is False
        assert info["client_type"] is None
        assert info["connection_time"] is None

    @patch("data.db.get_supabase_client")
    async def test_database_transaction_support(self, mock_get_client):
        """트랜잭션 지원 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        Database._client = mock_client
        Database._initialized = True

        db = Database()

        # 트랜잭션 시작/커밋/롤백 메서드가 있는지 확인
        assert hasattr(db, "begin_transaction")
        assert hasattr(db, "commit_transaction")
        assert hasattr(db, "rollback_transaction")

    @patch("data.db.get_supabase_client")
    def test_database_multiple_instances_same_client(self, mock_get_client):
        """여러 Database 인스턴스가 같은 클라이언트를 공유하는지 테스트"""
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        Database._client = mock_client
        Database._initialized = True

        db1 = Database()
        db2 = Database()

        # 같은 클라이언트를 공유하는지 확인
        assert db1.get_client() is db2.get_client()
        assert db1.get_client() is mock_client
