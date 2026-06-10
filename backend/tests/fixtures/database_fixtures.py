# tests/fixtures/database_fixtures.py
"""
데이터베이스 관련 테스트 fixtures
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import AsyncGenerator, Dict, Any
from supabase import Client
from data.db import Database


@pytest.fixture
async def mock_supabase_response() -> Dict[str, Any]:
    """표준 Supabase 응답 형식"""
    return {"data": [], "error": None, "count": 0, "status": 200, "status_text": "OK"}


@pytest.fixture
async def successful_supabase_response(mock_supabase_response) -> Dict[str, Any]:
    """성공적인 Supabase 응답"""
    mock_supabase_response["data"] = [{"id": 1, "status": "success"}]
    mock_supabase_response["count"] = 1
    return mock_supabase_response


@pytest.fixture
async def error_supabase_response(mock_supabase_response) -> Dict[str, Any]:
    """에러가 있는 Supabase 응답"""
    mock_supabase_response["error"] = {
        "message": "Test error",
        "details": "Test error details",
        "hint": "Test hint",
        "code": "42000",
    }
    mock_supabase_response["status"] = 400
    mock_supabase_response["status_text"] = "Bad Request"
    return mock_supabase_response


@pytest.fixture
def mock_supabase_table_operations():
    """Supabase 테이블 연산 Mock"""
    mock_table = MagicMock()

    # Select operations
    mock_select = MagicMock()
    mock_select.eq.return_value = mock_select
    mock_select.neq.return_value = mock_select
    mock_select.gt.return_value = mock_select
    mock_select.gte.return_value = mock_select
    mock_select.lt.return_value = mock_select
    mock_select.lte.return_value = mock_select
    mock_select.like.return_value = mock_select
    mock_select.ilike.return_value = mock_select
    mock_select.in_.return_value = mock_select
    mock_select.is_.return_value = mock_select
    mock_select.filter.return_value = mock_select
    mock_select.order.return_value = mock_select
    mock_select.limit.return_value = mock_select
    mock_select.offset.return_value = mock_select
    mock_select.range.return_value = mock_select
    mock_select.single.return_value = mock_select
    mock_select.maybe_single.return_value = mock_select
    mock_select.execute.return_value = AsyncMock()

    mock_table.select.return_value = mock_select

    # Insert operations
    mock_insert = MagicMock()
    mock_insert.execute.return_value = AsyncMock()
    mock_table.insert.return_value = mock_insert

    # Update operations
    mock_update = MagicMock()
    mock_update.eq.return_value = mock_update
    mock_update.execute.return_value = AsyncMock()
    mock_table.update.return_value = mock_update

    # Delete operations
    mock_delete = MagicMock()
    mock_delete.eq.return_value = mock_delete
    mock_delete.execute.return_value = AsyncMock()
    mock_table.delete.return_value = mock_delete

    # Upsert operations
    mock_upsert = MagicMock()
    mock_upsert.execute.return_value = AsyncMock()
    mock_table.upsert.return_value = mock_upsert

    return mock_table


@pytest.fixture
async def isolated_database() -> AsyncGenerator[Database, None]:
    """격리된 테스트용 데이터베이스"""
    # 실제 데이터베이스 연결 대신 Mock 사용
    with patch("data.db.get_supabase_client") as mock_get_client:
        mock_client = MagicMock(spec=Client)
        mock_get_client.return_value = mock_client

        # Database 싱글톤 초기화
        Database._instance = None
        Database._client = None
        Database._initialized = False

        db = Database()
        await db.initialize()

        yield db

        # 정리
        Database._instance = None
        Database._client = None
        Database._initialized = False


@pytest.fixture
def db_health_check_response() -> Dict[str, Any]:
    """DB 헬스체크 응답"""
    return {"status": "healthy", "connected": True, "timestamp": "2024-01-01T00:00:00Z", "database": "test_db"}
