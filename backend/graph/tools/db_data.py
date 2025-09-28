# tools/db_data.py
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.tools import tool
from repo import get_portfolio_repo, get_transaction_repo, get_user_repo
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import ToolException

logger = logging.getLogger(__name__)


def get_user_id_from_config(config: Optional[RunnableConfig]) -> int:
    """현재 실행 컨텍스트에서 user_id를 가져옵니다"""
    if not config:
        # 런타임에서 config가 비어 들어온 경우
        raise ToolException("Missing runtime config. `configurable.user_id` cannot be resolved.")

    cfg = config.get("configurable") or {}
    if "user_id" not in cfg:
        raise ToolException("`configurable.user_id` is not set in RunnableConfig.")

    user_id = cfg.get("user_id")
    # 0 같은 값도 합법일 수도 있겠지만, 보통은 정수/양수. 필요시 엄격 검증:
    if user_id is None:
        raise ToolException("`configurable.user_id` resolved to None.")
    if not isinstance(user_id, int):
        raise ToolException(f"`configurable.user_id` must be int, got {type(user_id).__name__}.")

    return user_id


@tool
def get_portfolio_history(config: RunnableConfig, days: int = 7) -> Dict[str, Any]:
    """
    지난 N일간의 포트폴리오 기록과 현재 포지션을 가져오는 도구

    Args:
        days: 가져올 기간 (기본 7일)

    Returns:
        Dict containing portfolio performance history and current positions
    """
    try:
        # config에서 user_id 가져오기
        user_id = get_user_id_from_config(config)

        # init Repo
        portfolio_repo = get_portfolio_repo()
        transaction_repo = get_transaction_repo()

        # get portfolio, positions, transactions
        portfolio = asyncio.run(portfolio_repo.get_by_user_id(user_id))
        positions = portfolio.positions
        transactions = asyncio.run(transaction_repo.get_recent_transactions(portfolio.id, days))

        return {
            "status": "success",
            "user_id": user_id,
            "portfolio_id": portfolio.id,
            "period_days": days,
            "portfolio": portfolio.model_dump(),
            "recent_transactions": [transaction.model_dump() for transaction in transactions],
            "summary": {
                "num_positions": len(positions),
                "top_holdings": [pos.ticker for pos in positions[:5]],
                "total_market_value": float(portfolio.total_stock_value),
                "total_value": float(portfolio.cash + portfolio.total_stock_value),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "database",
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@tool
def get_current_portfolio(config: RunnableConfig) -> Dict[str, Any]:
    """
    현재 포트폴리오 완전한 정보 조회 (Agent 파이프라인용)

    Returns:
        Dict containing complete current portfolio information
    """
    try:
        # config에서 user_id 가져오기
        user_id = get_user_id_from_config(config)

        # init Repo
        portfolio_repo = get_portfolio_repo()

        portfolio = asyncio.run(portfolio_repo.get_by_user_id(user_id))

        # Agent 파이프라인용 universe 및 portfolio 구성
        universe = [pos.ticker for pos in portfolio.positions]

        return {
            "status": "success",
            "user_id": user_id,
            "portfolio": portfolio.model_dump(),
            "universe": universe,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@tool
def get_user_profile(config: RunnableConfig) -> Dict[str, Any]:
    """
    사용자 프로필 정보 조회

    Returns:
        Dict containing user profile information
    """
    try:
        # config에서 user_id 가져오기
        user_id = get_user_id_from_config(config)

        # init Repo
        user_repo = get_user_repo()

        user_info = asyncio.run(user_repo.get_by_id(user_id))

        if not user_info:
            return {
                "status": "error",
                "error": "User not found",
                "timestamp": datetime.utcnow().isoformat(),
            }

        return {
            "status": "success",
            "user": user_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
