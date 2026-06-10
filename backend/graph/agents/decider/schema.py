# agents/decider/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel
from data.schemas import PortfolioOut


class Decision(BaseModel):
    ticker: str
    action: str  # 'BUY' | 'SELL' | 'HOLD' | 'TRIM'
    target_weight_pct: float
    current_weight_pct: float
    shares_to_trade: float
    trade_value: float
    total_score: float
    momo_score: float
    fund_score: float
    reason: str
    risk_notes: List[str]


class DeciderLLMDecision(BaseModel):
    """LLM이 결정하는 것은 액션/목표비중/근거뿐.

    수량·금액·점수·현재비중은 코드가 실제 포트폴리오와 시세로 계산한다 (환각 경로 차단).
    """

    ticker: str
    action: str  # 'BUY' | 'SELL' | 'HOLD' | 'TRIM'
    target_weight_pct: float
    reason: str
    risk_notes: List[str] = []


class DeciderLLMOutput(BaseModel):
    decisions: List[DeciderLLMDecision]


class DeciderState(BaseModel):
    asof: str
    universe: List[str]
    new_candidates: List[Dict[str, Any]]
    momo_score: List[Dict[str, Any]]
    fund_score: List[Dict[str, Any]]
    review_note: Dict[str, Any]
    risk_note: Dict[str, Any]
    decisions: List[Decision] | None = None  # 출력: 매매 결정들
    final_portfolio: PortfolioOut | None = None  # 출력: 최종 포트폴리오
    risk_end: bool = False
