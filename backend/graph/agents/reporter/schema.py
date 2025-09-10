# agents/reporter/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel
from schemas import PortfolioOut


class ReporterState(BaseModel):
    asof: str
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    momo_score: List[Dict[str, Any]]
    fund_score: List[Dict[str, Any]]
    review_note: Dict[str, Any]
    risk_note: Dict[str, Any]
    final_portfolio: PortfolioOut
    language: str = "ko"
    report_md: str | None = None


class ReporterOutput(BaseModel):
    report_md: str
