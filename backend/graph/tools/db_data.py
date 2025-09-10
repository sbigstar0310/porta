# tools/db_data.py

import asyncio
from typing import Dict, Any
from datetime import datetime
from langchain_core.tools import tool
from repo.user_repo import UserRepo
from repo.portfolio_repo import PortfolioRepo
from repo.transaction_repo import TransactionRepo


@tool
def get_portfolio_history(user_id: int = 1, days: int = 7) -> Dict[str, Any]:
    """
    지난 N일간의 포트폴리오 기록과 현재 포지션을 가져오는 도구

    Args:
        user_id: 사용자 ID (기본 1)
        days: 가져올 기간 (기본 7일)

    Returns:
        Dict containing portfolio performance history and current positions
    """
    try:
        # init Repo
        portfolio_repo = PortfolioRepo()
        transaction_repo = TransactionRepo()

        # get portfolio, positions, transactions
        portfolio = asyncio.run(portfolio_repo.get_current_portfolio(user_id))
        positions = portfolio.positions
        transactions = asyncio.run(
            transaction_repo.get_recent_transactions(portfolio.id, days)
        )

        return {
            "status": "success",
            "user_id": user_id,
            "portfolio_id": portfolio.id,
            "period_days": days,
            "portfolio": portfolio.model_dump(),
            "recent_transactions": [
                transaction.model_dump() for transaction in transactions
            ],
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
def get_current_portfolio(user_id: int = 1) -> Dict[str, Any]:
    """
    현재 포트폴리오 완전한 정보 조회 (Agent 파이프라인용)

    Args:
        user_id: 사용자 ID (기본 1)

    Returns:
        Dict containing complete current portfolio information
    """
    try:
        # init Repo
        portfolio_repo = PortfolioRepo()

        portfolio = asyncio.run(portfolio_repo.get_current_portfolio(user_id))

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
def get_user_profile(user_id: int = 1) -> Dict[str, Any]:
    """
    사용자 프로필 정보 조회

    Args:
        user_id: 사용자 ID (기본 1)

    Returns:
        Dict containing user profile information
    """
    try:
        # init Repo
        user_repo = UserRepo()

        user_info = asyncio.run(user_repo.get_user_info(user_id))

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
