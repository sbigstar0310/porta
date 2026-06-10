# tests/fixtures/agent_fixtures.py
"""
Agent 관련 테스트 fixtures
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List
from datetime import datetime, timezone

from graph.llm_clients.mock_client import MockLLMClient
from graph.tools.web_search import web_search_ddg
from graph.tools.stock_data import get_stock_data
from graph.tools.db_data import get_portfolio_data


@pytest.fixture
def mock_llm_response() -> str:
    """기본 LLM 응답"""
    return "This is a mock LLM response for testing purposes."


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Mock OpenAI 클라이언트"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mock OpenAI response"
    mock_client.invoke.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Mock Anthropic 클라이언트"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mock Anthropic response"
    mock_client.invoke.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Mock LLM 클라이언트 (실제 MockLLMClient 사용)"""
    return MockLLMClient()


@pytest.fixture
def sample_web_search_result() -> str:
    """샘플 웹 검색 결과"""
    return """
    Search Results:
    1. Apple Inc. Stock Analysis - Recent earnings show strong performance with Q4 revenue up 8%.
    2. Market Trends - Technology stocks showing bullish momentum in current market conditions.
    3. Analyst Reports - AAPL target price raised to $200 by Goldman Sachs.
    """


@pytest.fixture
def sample_stock_data_result() -> Dict[str, Any]:
    """샘플 주식 데이터 결과"""
    return {
        "status": "success",
        "stock_history": {
            "AAPL": {
                "2024-01-01": {"Open": 150.0, "High": 155.0, "Low": 148.0, "Close": 152.0, "Volume": 1000000},
                "2024-01-02": {"Open": 152.0, "High": 157.0, "Low": 151.0, "Close": 155.0, "Volume": 1100000},
            }
        },
        "stock_info": {
            "AAPL": {
                "symbol": "AAPL",
                "shortName": "Apple Inc.",
                "currentPrice": 155.0,
                "marketCap": 2400000000000,
                "trailingPE": 25.5,
                "forwardPE": 22.8,
            }
        },
    }


@pytest.fixture
def sample_portfolio_data_result() -> Dict[str, Any]:
    """샘플 포트폴리오 데이터 결과"""
    return {
        "status": "success",
        "portfolios": [
            {
                "id": 1,
                "name": "Tech Growth Portfolio",
                "total_value": 50000.0,
                "positions": [
                    {"symbol": "AAPL", "shares": 100, "current_price": 155.0, "market_value": 15500.0},
                    {"symbol": "MSFT", "shares": 80, "current_price": 375.0, "market_value": 30000.0},
                ],
            }
        ],
    }


@pytest.fixture
def mock_web_search_tool() -> MagicMock:
    """Mock 웹 검색 도구"""
    with patch("graph.tools.web_search.web_search_ddg") as mock_tool:
        mock_tool.return_value = "Mock web search results"
        yield mock_tool


@pytest.fixture
def mock_stock_data_tool() -> MagicMock:
    """Mock 주식 데이터 도구"""
    with patch("graph.tools.stock_data.get_stock_data") as mock_tool:
        mock_tool.return_value = {
            "status": "success",
            "stock_history": {"AAPL": {}},
            "stock_info": {"AAPL": {"currentPrice": 155.0}},
        }
        yield mock_tool


@pytest.fixture
def mock_db_data_tool() -> MagicMock:
    """Mock DB 데이터 도구"""
    with patch("graph.tools.db_data.get_portfolio_data") as mock_tool:
        mock_tool.return_value = {"status": "success", "portfolios": []}
        yield mock_tool


@pytest.fixture
def crawler_state_sample() -> Dict[str, Any]:
    """Crawler 에이전트 상태 샘플"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": [],
        "messages": [],
        "search_results": [],
    }


@pytest.fixture
def momo_state_sample() -> Dict[str, Any]:
    """Momentum 에이전트 상태 샘플"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": ["NVDA"],
        "messages": [],
        "momentum_scores": [
            {"symbol": "AAPL", "score": 0.75, "trend": "bullish"},
            {"symbol": "MSFT", "score": 0.68, "trend": "bullish"},
        ],
    }


@pytest.fixture
def fund_state_sample() -> Dict[str, Any]:
    """Fundamental 에이전트 상태 샘플"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": ["NVDA"],
        "messages": [],
        "fundamental_analysis": [
            {"symbol": "AAPL", "pe_ratio": 25.5, "revenue_growth": 0.08, "rating": "BUY"},
            {"symbol": "MSFT", "pe_ratio": 28.2, "revenue_growth": 0.12, "rating": "BUY"},
        ],
    }


@pytest.fixture
def risk_state_sample() -> Dict[str, Any]:
    """Risk 에이전트 상태 샘플"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": ["NVDA"],
        "messages": [],
        "risk_metrics": {"portfolio_beta": 1.2, "max_drawdown": 0.15, "var_95": 0.12},
        "risk_warnings": [],
    }


@pytest.fixture
def decider_state_sample() -> Dict[str, Any]:
    """Decider 에이전트 상태 샘플"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": ["NVDA"],
        "messages": [],
        "decisions": [{"symbol": "NVDA", "action": "BUY", "weight": 0.1, "confidence": 0.85}],
        "rationale": "Strong momentum and fundamentals support adding NVDA to portfolio",
    }


@pytest.fixture
def reporter_state_sample() -> Dict[str, Any]:
    """Reporter 에이전트 상태 샘플"""
    return {
        "asof": datetime.now(timezone.utc).isoformat(),
        "universe": ["AAPL", "MSFT", "GOOGL"],
        "new_candidates": ["NVDA"],
        "messages": [],
        "report": "# Portfolio Analysis Report\n\nMarket analysis shows positive trends...",
        "sections": ["market_overview", "individual_analysis", "recommendations"],
    }


@pytest.fixture
def all_tools_mocked():
    """모든 도구가 Mock된 상태"""
    with patch("graph.tools.web_search.web_search_ddg") as mock_web, patch(
        "graph.tools.stock_data.get_stock_data"
    ) as mock_stock, patch("graph.tools.db_data.get_portfolio_data") as mock_db:

        mock_web.return_value = "Mock web search results"
        mock_stock.return_value = {"status": "success", "data": {}}
        mock_db.return_value = {"status": "success", "portfolios": []}

        yield {"web_search": mock_web, "stock_data": mock_stock, "db_data": mock_db}


@pytest.fixture
def agent_execution_context():
    """에이전트 실행 컨텍스트"""
    return {
        "user_id": 1,
        "portfolio_id": 1,
        "analysis_date": datetime.now(timezone.utc),
        "market_hours": True,
        "debug_mode": True,
    }
