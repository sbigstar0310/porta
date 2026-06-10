# agents/momo/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict


class MomoFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    r20: float  # 최근 20일 수익률
    r60: float  # 최근 60일 수익률
    ma_cross: bool  # 이동평균선 교차 여부
    breakout: bool  # 돌파 여부
    vol_surge: float  # 거래량 급증 비율
    atr_pct_14: float  # 14일간 변동성 비율


class MomoNorm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    z20: float  # 최근 20일 수익률 정규화
    z60: float  # 최근 60일 수익률 정규화
    zvol: float  # 거래량 급증 비율 정규화


class MomoScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    MOMO: float
    features: MomoFeatures
    norm: MomoNorm
    data_confidence: str  # "high" | "medium" | "low"


class MomoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    score: MomoScore
    comment: str = ""  # LLM이 작성한 해석 (숫자는 도구 원본만 사용)
    caveats: List[str] = []  # 데이터 품질/이벤트 관련 주의점


class MomoState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asof: str
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    momo_score: List[MomoItem] = []


class MomoCommentary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    comment: str
    caveats: List[str] = []


class MomoCommentaryOutput(BaseModel):
    """LLM 출력은 해석만 담는다. 숫자 필드를 두지 않아 환각 경로 자체를 차단한다."""

    model_config = ConfigDict(extra="forbid")
    commentary: List[MomoCommentary]
