# tests/conftest.py
"""
테스트 공통 설정 및 fixtures
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import tempfile
from datetime import datetime, timezone

# 테스트 환경 변수 설정
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-supabase-key"

from app import app
from data.db import Database
from supabase import Client


@pytest.fixture(scope="session")
def event_loop():
    """세션 스코프의 이벤트 루프 생성"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """FastAPI 테스트 클라이언트"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def mock_supabase_client() -> AsyncGenerator[MagicMock, None]:
    """Mock Supabase 클라이언트"""
    mock_client = MagicMock(spec=Client)

    # 기본 Mock 응답 설정
    mock_client.table.return_value.select.return_value.execute.return_value.data = []
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": 1}]
    mock_client.table.return_value.update.return_value.execute.return_value.data = [{"id": 1}]
    mock_client.table.return_value.delete.return_value.execute.return_value.data = [{"id": 1}]

    yield mock_client


@pytest.fixture
async def mock_database(mock_supabase_client) -> AsyncGenerator[Database, None]:
    """Mock Database 인스턴스"""
    with patch("data.db.Database._client", mock_supabase_client):
        with patch("data.db.Database._initialized", True):
            db = Database()
            yield db


@pytest.fixture
def sample_user_data() -> dict:
    """테스트용 사용자 데이터"""
    return {
        "id": 1,
        "uuid": "test-uuid-123",
        "email": "test@example.com",
        "timezone": "Asia/Seoul",
        "language": "ko",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_portfolio_data() -> dict:
    """테스트용 포트폴리오 데이터"""
    return {
        "id": 1,
        "user_id": 1,
        "name": "테스트 포트폴리오",
        "description": "테스트용 포트폴리오입니다",
        "total_value": 10000.00,
        "currency": "USD",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_position_data() -> dict:
    """테스트용 포지션 데이터"""
    return {
        "id": 1,
        "portfolio_id": 1,
        "symbol": "AAPL",
        "shares": 10.0,
        "average_price": 150.00,
        "current_price": 155.00,
        "market_value": 1550.00,
        "unrealized_gain_loss": 50.00,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_transaction_data() -> dict:
    """테스트용 거래 데이터"""
    return {
        "id": 1,
        "portfolio_id": 1,
        "symbol": "AAPL",
        "transaction_type": "buy",
        "shares": 10.0,
        "price": 150.00,
        "total_amount": 1500.00,
        "transaction_date": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_stock_data() -> dict:
    """테스트용 주식 데이터"""
    return {
        "status": "success",
        "stock_history": {
            "AAPL": {"2024-01-01": {"Open": 150.0, "High": 155.0, "Low": 148.0, "Close": 152.0, "Volume": 1000000}}
        },
        "stock_info": {
            "AAPL": {"symbol": "AAPL", "shortName": "Apple Inc.", "currentPrice": 152.0, "marketCap": 2400000000000}
        },
    }


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Mock LLM 클라이언트"""
    mock_client = MagicMock()
    mock_client.invoke.return_value = MagicMock(content="Mock LLM response")
    return mock_client


@pytest.fixture
def sample_agent_state() -> dict:
    """테스트용 Agent State"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": [],
        "messages": [],
    }


@pytest.fixture(autouse=True)
async def cleanup_database():
    """테스트 후 데이터베이스 정리"""
    yield
    # 테스트 후 정리 로직 (필요시)
    pass


# Agent 테스트용 fixtures
@pytest.fixture
def mock_web_search_tool() -> MagicMock:
    """Mock 웹 검색 도구"""
    mock_tool = MagicMock()
    mock_tool.invoke.return_value = "Mock search results"
    return mock_tool


@pytest.fixture
def mock_stock_tool() -> MagicMock:
    """Mock 주식 데이터 도구"""
    mock_tool = MagicMock()
    mock_tool.invoke.return_value = {"status": "success", "data": {"AAPL": {"price": 150.0}}}
    return mock_tool


@pytest.fixture
def mock_db_tool() -> MagicMock:
    """Mock DB 데이터 도구"""
    mock_tool = MagicMock()
    mock_tool.invoke.return_value = {"status": "success", "data": []}
    return mock_tool


# 성능 테스트용 fixtures
@pytest.fixture
def performance_timer():
    """성능 측정용 타이머"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# 테스트 마커 자동 적용
def pytest_configure(config):
    """pytest 설정"""
    # 각 테스트 파일에 자동으로 마커 적용
    config.addinivalue_line("markers", "unit: 단위 테스트")
    config.addinivalue_line("markers", "integration: 통합 테스트")
    config.addinivalue_line("markers", "performance: 성능 테스트")
    config.addinivalue_line("markers", "e2e: End-to-End 테스트")


def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 자동 마커 적용"""
    for item in items:
        # 파일 경로에 따라 자동으로 마커 적용
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "agent" in str(item.fspath):
            item.add_marker(pytest.mark.agent)
