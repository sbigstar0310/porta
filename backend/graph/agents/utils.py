# agents/utils.py
"""에이전트 공용 헬퍼.

설계 원칙: 숫자(ground truth)는 도구 원본에서만 읽고, LLM 출력에서는 해석/판단만 신뢰한다.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Template

logger = logging.getLogger(__name__)


def load_template(module_file: str, filename: str = "system_prompt.md") -> Template:
    """에이전트 모듈과 같은 디렉토리에 있는 Jinja 템플릿을 로드한다."""
    directory = os.path.dirname(os.path.abspath(module_file))
    with open(os.path.join(directory, filename), "r") as f:
        return Template(f.read())


def state_get(state: Any, key: str, default: Any = None) -> Any:
    """LangGraph state가 dict든 Pydantic 모델이든 동일하게 값을 읽는다."""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def extract_structured_response(out: Any) -> Dict[str, Any]:
    """에이전트 출력의 structured_response를 dict로 정규화한다 (없으면 빈 dict)."""
    structured = out.get("structured_response") if isinstance(out, dict) else None
    if structured is None:
        return {}
    if not isinstance(structured, dict):
        structured = structured.model_dump()
    return structured


def extract_last_tool_result(messages: Optional[List[Any]], tool_name: str) -> Optional[Dict[str, Any]]:
    """
    에이전트 메시지 기록에서 특정 도구의 마지막 ToolMessage 원본 결과를 파싱합니다.

    LLM이 structured output으로 옮겨 적은 숫자 대신, 도구가 실제로 반환한
    원본 값(ground truth)을 사용하기 위한 헬퍼입니다.
    """
    for message in reversed(messages or []):
        if getattr(message, "type", None) != "tool":
            continue
        if getattr(message, "name", None) != tool_name:
            continue

        content = message.content
        if isinstance(content, dict):
            return content
        if isinstance(content, list):
            # content blocks 형태인 경우 텍스트 블록을 이어 붙임
            content = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block) for block in content
            )
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
        except (TypeError, ValueError):
            logger.warning(f"Failed to parse tool message content for `{tool_name}`")
            return None
    return None


def run_commentary_agent(
    agent: Any,
    state: Any,
    config: Any,
    tool_name: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """ReAct 에이전트를 실행해 (도구 원본 결과, 티커별 해석)을 반환한다.

    실패해도 예외를 던지지 않는다 — 호출 측은 ensure_tool_result()로 숫자만이라도 확보한다.
    """
    try:
        out = agent.invoke(messages=[], input=state, config=config)
    except Exception as e:
        logger.error(f"Agent invocation failed (tool={tool_name}), falling back to direct tool call: {e}")
        return None, {}

    tool_result = extract_last_tool_result(out.get("messages", []), tool_name)
    commentary_by_ticker = {
        c.get("ticker", ""): c for c in extract_structured_response(out).get("commentary", [])
    }
    return tool_result, commentary_by_ticker


def ensure_tool_result(
    tool_result: Optional[Dict[str, Any]],
    tool: Any,
    result_key: str,
    tickers: List[str],
    period: str = "6mo",
) -> Optional[Dict[str, Any]]:
    """ToolMessage에서 유효한 결과를 얻지 못했으면 도구를 직접 호출해 ground truth를 확보한다."""
    if tool_result and tool_result.get("status") != "error" and result_key in tool_result:
        return tool_result
    if not tickers:
        return None

    fallback = tool.invoke({"tickers": tickers, "period": period})
    if not fallback or fallback.get("status") == "error":
        logger.error(f"Tool `{tool.name}` failed: {fallback}")
        return None
    return fallback


def apply_commentary(items: List[Any], commentary_by_ticker: Dict[str, Dict[str, Any]]) -> None:
    """숫자는 도구 원본 그대로 두고, LLM 해석(comment/caveats)만 병합한다."""
    for item in items:
        commentary = commentary_by_ticker.get(item.ticker)
        if commentary:
            item.comment = str(commentary.get("comment", ""))
            item.caveats = [str(caveat) for caveat in commentary.get("caveats", [])]


def candidate_tickers(universe: List[str], new_candidates: List[Dict[str, Any]]) -> List[str]:
    """유니버스 + 신규 후보의 전체 티커 목록."""
    return list(universe) + [c.get("ticker") for c in new_candidates if c.get("ticker")]
