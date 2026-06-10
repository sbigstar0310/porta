# agents/reviewer/schema.py
from typing import Any, Dict
from pydantic import BaseModel


class ReviewerNote(BaseModel):
    period: str
    opinion: str  # LLM이 작성한 성과 해석
    preference: str  # "momentum" | "balanced" | "fundamental" (δ에서 코드가 도출)
    adjustment: float  # δ — 트랙레코드 통계로 코드가 산출 (graph/feedback.py)
    scorecard: Dict[str, Any] = {}  # 적중률/초과수익 통계 (보고서 성적표에 사용)


class ReviewerState(BaseModel):
    user_id: int
    asof: str
    review_note: ReviewerNote | None = None


class ReviewerNarrative(BaseModel):
    """LLM 출력은 해석만 담는다. δ·통계는 코드가 계산한다."""

    opinion: str
