# llm_clients/openai_client.py
from __future__ import annotations

import os
from enum import Enum

from langchain_openai import ChatOpenAI


class LLMTier(str, Enum):
    """추론 부하에 따른 모델 티어(LIGHT < MIDDLE < HEAVY). tier 값을 바꾸면 해당 tier를 쓰는 모든 에이전트에 일괄 반영된다."""

    LIGHT = "light"
    MIDDLE = "middle"
    HEAVY = "heavy"


# tier → 실제 모델명. 모델 교체는 이 표 한 곳만 수정하면 된다.
TIER_MODELS: dict[LLMTier, str] = {
    LLMTier.LIGHT: "gpt-5.4-nano",
    LLMTier.MIDDLE: "gpt-5.4-mini",
    LLMTier.HEAVY: "gpt-5.4",
}


def _resolve_model(model: str | LLMTier) -> str:
    """tier(enum 또는 'light' 같은 문자열)면 매핑하고, 그 외에는 모델명으로 그대로 사용한다."""
    if isinstance(model, LLMTier):
        return TIER_MODELS[model]
    try:
        return TIER_MODELS[LLMTier(model)]  # 'light' 같은 tier 문자열도 허용
    except ValueError:
        return model  # 'gpt-4o' 같은 직접 지정 모델명


def get_openai_client(
    model: str | LLMTier = LLMTier.LIGHT,
    temperature: float = 0.1,
) -> ChatOpenAI:
    """tier 또는 모델명을 받아 ChatOpenAI 클라이언트를 생성한다.

    Args:
        model: LLMTier, 'light' 같은 tier 문자열, 또는 'gpt-4o' 같은 직접 모델명
        temperature: 샘플링 온도

    Returns:
        ChatOpenAI 인스턴스
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
            "다음 명령어로 설정하세요: export OPENAI_API_KEY='your-api-key'"
        )

    return ChatOpenAI(model=_resolve_model(model), temperature=temperature, api_key=api_key)
