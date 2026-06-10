# Repository Layer Dependency Injection
from supabase import Client
from clients import get_stock_client, get_supabase_admin_client

from .user_repo import UserRepo
from .portfolio_repo import PortfolioRepo
from .position_repo import PositionRepo
from .report_repo import ReportRepo
from .transaction_repo import TransactionRepo
from .schedule_repo import ScheduleRepo
from .recommendation_repo import RecommendationRepo


# Database 의존성 주입
def get_db_client() -> Client:
    """
    데이터 계층(Repository)용 Supabase 클라이언트를 반환한다.

    백엔드는 자체 JWT 인증(get_current_user_id)으로 접근을 통제하고 쿼리에
    user_id 를 명시하므로, 데이터 R/W 는 service_role 키(admin 클라이언트)를
    사용해 RLS 를 우회한다. 인증(GoTrue) 작업은 별도로 anon 키(SUPABASE_KEY)를
    쓰는 get_supabase_client() 를 사용한다.
    """
    return get_supabase_admin_client()


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


def get_position_repo() -> PositionRepo:
    """
    PositionRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    db_client = get_db_client()
    stock_client = get_stock_client()
    return PositionRepo(db_client=db_client, stock_client=stock_client)


def get_transaction_repo() -> TransactionRepo:
    """
    TransactionRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    db_client = get_db_client()
    return TransactionRepo(db_client=db_client)


def get_report_repo() -> ReportRepo:
    """
    ReportRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    db_client = get_db_client()
    return ReportRepo(db_client=db_client)


def get_schedule_repo() -> ScheduleRepo:
    """
    ScheduleRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    db_client = get_db_client()
    return ScheduleRepo(db_client=db_client)


def get_recommendation_repo() -> RecommendationRepo:
    """
    RecommendationRepo 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    db_client = get_db_client()
    return RecommendationRepo(db_client=db_client)


# 모든 Repo 팩토리 함수들을 외부에서 import할 수 있도록 export
__all__ = [
    "get_db_client",
    "get_user_repo",
    "get_portfolio_repo",
    "get_position_repo",
    "get_report_repo",
    "get_schedule_repo",
    "get_recommendation_repo",
    "UserRepo",
    "PortfolioRepo",
    "PositionRepo",
    "ReportRepo",
    "ScheduleRepo",
    "RecommendationRepo",
]
