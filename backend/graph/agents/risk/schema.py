# agents/risk/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel


class SectorCap(BaseModel):
    sector: str
    cap: float


class PerTicker(BaseModel):
    ticker: str
    allowed: bool
    max_weight_pct: float
    notes: List[str]
    beta: float
    atr_pct: float


class PortfolioLimits(BaseModel):
    single_stock_cap: float
    sector_caps: List[SectorCap]
    cash_floor: float


class PortfolioWarnings(BaseModel):
    type: str
    sector: str
    actual: float
    limit: float


class RiskNote(BaseModel):
    per_ticker: List[PerTicker]
    portfolio_limits: PortfolioLimits
    portfolio_warnings: List[PortfolioWarnings]
    overall_note: str


class RiskState(BaseModel):
    asof: str
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    momo_score: List[Dict[str, Any]]
    fund_score: List[Dict[str, Any]]
    risk_note: RiskNote | None = None


class RiskOutput(BaseModel):
    risk_note: RiskNote
