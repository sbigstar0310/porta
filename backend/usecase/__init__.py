# UseCase Layer Dependency Injection
from repo import UserRepo, get_user_repo

from .user_usecase import UserUsecase


# UseCase 팩토리 함수들
def get_user_usecase() -> UserUsecase:
    """
    UserUsecase 인스턴스를 반환하는 팩토리 함수
    FastAPI의 Depends와 함께 사용할 수 있습니다.
    """
    user_repo = get_user_repo()
    return UserUsecase(user_repo)


# 모든 UseCase 팩토리 함수들을 외부에서 import할 수 있도록 export
__all__ = ["get_user_usecase", "UserUsecase"]
