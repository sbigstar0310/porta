# agents/fund/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")
    V: int = Field(ge=0, le=100)
    G: int = Field(ge=0, le=100)
    Q: int = Field(ge=0, le=100)
    E: int = Field(ge=0, le=100)


class FundItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    FUND: int
    scores: ScoreBreakdown
    label: str  # "Strong" | "Neutral" | "Weak"
    insights: List[str]
    data_confidence: str  # "high" | "medium" | "low"
    comment: str = ""  # LLM이 작성한 해석 (숫자는 도구 원본만 사용)
    caveats: List[str] = []  # 데이터 품질/이벤트 관련 주의점


class FundState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    asof: str
    fund_score: List[FundItem] = []


class FundCommentary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    comment: str
    caveats: List[str] = []


class FundCommentaryOutput(BaseModel):
    """LLM 출력은 해석만 담는다. 숫자 필드를 두지 않아 환각 경로 자체를 차단한다."""

    model_config = ConfigDict(extra="forbid")
    commentary: List[FundCommentary]
