# graph/schemas.py
from typing import TypedDict, List, Dict, Any
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from schemas import PortfolioOut


class ParentState(TypedDict, total=False):
    # 최소 공유 채널
    messages: Annotated[List[Dict[str, Any]], add_messages]

    # 입력
    portfolio: PortfolioOut  # 현재 보유자산/현금 등
    universe: List[str]  # 현재 보유 티커들
    asof: str  # 데이터 기준시각
    language: str  # 유저 언어 설정 추가

    # Result of Agents
    new_candidates: List[Dict[str, Any]] = []  # Crawler에서 발견한 신규 후보
    momo_score: List[Dict[str, Any]] = []  # Momo 점수들
    fund_score: List[Dict[str, Any]] = []  # Fund 점수들
    review_note: Dict[str, Any] = {}  # Reviewer 노트
    risk_note: Dict[str, Any] = {}  # Risk Manager 노트
    decisions: List[Dict[str, Any]] = []  # Decider 매매 결정들
    final_portfolio: PortfolioOut | None = None  # Decider 최종 포트폴리오
    report_md: str | None = None  # Reporter 최종 리포트 마크다운
