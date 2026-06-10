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


class StockComment(BaseModel):
    ticker: str
    comment: str


class ReporterNarrative(BaseModel):
    """LLM 출력은 서술만 담는다. 수치(점수/비중/수량/금액)는 코드가 템플릿에 주입한다."""

    tldr: str
    stock_comments: List[StockComment]
    market_outlook: str
