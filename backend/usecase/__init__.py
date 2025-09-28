# UseCase Layer Dependency Injection
from repo import get_user_repo, get_portfolio_repo, get_position_repo, get_report_repo
from clients import get_supabase_client
from .portfolio_usecase import PortfolioUsecase
from .user_usecase import UserUsecase
from .position_usecase import PositionUsecase
from .report_usecase import ReportUsecase
from .task_usecase import TaskUsecase



# UseCase 팩토리 함수들
def get_user_usecase() -> UserUsecase:
    """
    UserUsecase 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    user_repo = get_user_repo()
    portfolio_repo = get_portfolio_repo()
    supabase_client = get_supabase_client()
    return UserUsecase(user_repo, portfolio_repo, supabase_client)


def get_portfolio_usecase() -> PortfolioUsecase:
    """
    PortfolioUsecase 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    portfolio_repo = get_portfolio_repo()
    return PortfolioUsecase(portfolio_repo)


def get_position_usecase() -> PositionUsecase:
    """
    PositionUsecase 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    position_repo = get_position_repo()
    return PositionUsecase(position_repo=position_repo)


def get_report_usecase() -> ReportUsecase:
    """
    ReportUsecase 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    report_repo = get_report_repo()
    return ReportUsecase(report_repo=report_repo)


def get_task_usecase() -> TaskUsecase:
    """
    TaskUsecase 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    return TaskUsecase()


# 모든 UseCase 팩토리 함수들을 외부에서 import할 수 있도록 export
__all__ = [
    "get_user_usecase",
    "UserUsecase",
    "get_portfolio_usecase",
    "PortfolioUsecase",
    "get_position_usecase",
    "PositionUsecase",
    "get_report_usecase",
    "ReportUsecase",
    "get_task_usecase",
    "TaskUsecase",
]

