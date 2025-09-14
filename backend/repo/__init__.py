# Repository Layer Dependency Injection
from supabase import Client
from clients import get_stock_client
from data.db import Database

from .user_repo import UserRepo
from .portfolio_repo import PortfolioRepo


# Database 의존성 주입
def get_db_client() -> Client:
    """
    Supabase 클라이언트를 반환하는 의존성 주입 함수
    """
    db = Database()
    return db.client


# Repository 팩토리 함수들
def get_user_repo() -> UserRepo:
    """
    UserRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    db_client = get_db_client()
    return UserRepo(db_client=db_client)


def get_portfolio_repo() -> PortfolioRepo:
    """
    PortfolioRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    stock_client = get_stock_client()
    db_client = get_db_client()
    return PortfolioRepo(stock_client=stock_client, db_client=db_client)


# 모든 Repo 팩토리 함수들을 외부에서 import할 수 있도록 export
__all__ = ["get_db_client", "get_user_repo", "get_portfolio_repo", "UserRepo", "PortfolioRepo"]
