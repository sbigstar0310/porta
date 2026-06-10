# agents/decider/schema.py
from typing import List, Dict, Any
from pydantic import BaseModel
from data.schemas import PortfolioOut


class Decision(BaseModel):
    ticker: str
    company_name: str = ""  # 보고서 표기용 회사명 (예: "Apple Inc.")
    action: str  # 'BUY' | 'SELL' | 'HOLD' | 'TRIM'
    target_weight_pct: float
    current_weight_pct: float
    shares_to_trade: float
    trade_value: float
    price: float = 0.0  # 검증에 사용된 시세 (추천 트랙레코드의 price_at_rec)
    confidence: float = 50.0  # LLM이 매긴 콜 적중 확신도 (0-100), Brier 보정 대상
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
    confidence: float = 50.0  # 이 콜이 맞을 확률에 대한 스스로의 평가 (0-100)
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
    market_regime: Dict[str, Any] = {}
    language: str = "ko"
    decisions: List[Decision] | None = None  # 출력: 매매 결정들
    final_portfolio: PortfolioOut | None = None  # 출력: 최종 포트폴리오
    risk_end: bool = False
