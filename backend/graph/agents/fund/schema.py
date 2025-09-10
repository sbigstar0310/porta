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


class FundState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    asof: str
    fund_score: List[FundItem] = []


class FundOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    asof: str
    fund_score: List[FundItem]
