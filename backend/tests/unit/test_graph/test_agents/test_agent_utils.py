# tests/unit/test_graph/test_agents/test_agent_utils.py
"""에이전트 공용 헬퍼(agents/utils.py) 단위 테스트"""
import json
import pytest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, ToolMessage
from pydantic import BaseModel

from graph.agents.utils import (
    apply_commentary,
    candidate_tickers,
    ensure_tool_result,
    extract_last_tool_result,
    extract_structured_response,
    state_get,
)


@pytest.mark.unit
class TestExtractLastToolResult:
    def test_parses_json_content(self):
        messages = [ToolMessage(content=json.dumps({"momo_score": []}), name="calc", tool_call_id="1")]
        assert extract_last_tool_result(messages, "calc") == {"momo_score": []}

    def test_picks_last_matching_tool_message(self):
        messages = [
            ToolMessage(content=json.dumps({"run": 1}), name="calc", tool_call_id="1"),
            ToolMessage(content=json.dumps({"run": 2}), name="calc", tool_call_id="2"),
        ]
        assert extract_last_tool_result(messages, "calc") == {"run": 2}

    def test_ignores_other_tools_and_ai_messages(self):
        messages = [
            AIMessage(content="hello"),
            ToolMessage(content=json.dumps({"x": 1}), name="other", tool_call_id="1"),
        ]
        assert extract_last_tool_result(messages, "calc") is None

    def test_invalid_json_returns_none(self):
        messages = [ToolMessage(content="not-json", name="calc", tool_call_id="1")]
        assert extract_last_tool_result(messages, "calc") is None

    def test_empty_messages(self):
        assert extract_last_tool_result([], "calc") is None
        assert extract_last_tool_result(None, "calc") is None


@pytest.mark.unit
class TestEnsureToolResult:
    def test_valid_result_passes_through(self):
        tool = MagicMock()
        result = {"momo_score": [{"ticker": "AAPL"}]}
        assert ensure_tool_result(result, tool, "momo_score", ["AAPL"]) == result
        tool.invoke.assert_not_called()

    def test_missing_result_triggers_direct_tool_call(self):
        tool = MagicMock()
        tool.invoke.return_value = {"momo_score": []}
        assert ensure_tool_result(None, tool, "momo_score", ["AAPL"]) == {"momo_score": []}
        tool.invoke.assert_called_once_with({"tickers": ["AAPL"], "period": "6mo"})

    def test_error_result_triggers_direct_tool_call(self):
        tool = MagicMock()
        tool.invoke.return_value = {"momo_score": []}
        assert ensure_tool_result({"status": "error"}, tool, "momo_score", ["AAPL"]) == {"momo_score": []}

    def test_fallback_error_returns_none(self):
        tool = MagicMock()
        tool.invoke.return_value = {"status": "error", "error": "boom"}
        assert ensure_tool_result(None, tool, "momo_score", ["AAPL"]) is None

    def test_no_tickers_returns_none(self):
        tool = MagicMock()
        assert ensure_tool_result(None, tool, "momo_score", []) is None
        tool.invoke.assert_not_called()


class _FakeItem:
    def __init__(self, ticker):
        self.ticker = ticker
        self.comment = ""
        self.caveats = []


@pytest.mark.unit
class TestApplyCommentary:
    def test_merges_comment_and_caveats(self):
        items = [_FakeItem("AAPL"), _FakeItem("TSLA")]
        apply_commentary(items, {"AAPL": {"comment": "good", "caveats": ["c1"]}})
        assert items[0].comment == "good" and items[0].caveats == ["c1"]
        assert items[1].comment == "" and items[1].caveats == []


class _FakeState(BaseModel):
    universe: list = ["AAPL"]


@pytest.mark.unit
class TestStateHelpers:
    def test_state_get_dict_and_model(self):
        assert state_get({"universe": ["AAPL"]}, "universe") == ["AAPL"]
        assert state_get(_FakeState(), "universe") == ["AAPL"]
        assert state_get({}, "missing", "default") == "default"

    def test_extract_structured_response(self):
        class Out(BaseModel):
            commentary: list = []

        assert extract_structured_response({"structured_response": Out()}) == {"commentary": []}
        assert extract_structured_response({"structured_response": {"a": 1}}) == {"a": 1}
        assert extract_structured_response({}) == {}

    def test_candidate_tickers(self):
        assert candidate_tickers(["AAPL"], [{"ticker": "NVDA"}, {"name": "no-ticker"}]) == ["AAPL", "NVDA"]
