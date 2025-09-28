# agents/reporter/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel
from data.schemas import PortfolioOut
from typing import Optional


class ReporterState(BaseModel):
    asof: str
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    momo_score: List[Dict[str, Any]]
    fund_score: List[Dict[str, Any]]
    review_note: Dict[str, Any]
    risk_note: Dict[str, Any]
    final_portfolio: Optional[PortfolioOut] = None
    language: str = "ko"
    report_md: str | None = None
    decider_end: bool = False


class ReporterOutput(BaseModel):
    report_md: str
