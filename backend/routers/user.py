from fastapi import APIRouter, Depends, HTTPException, status
from usecase import UserUsecase, get_user_usecase
from data.schemas import UserOut, UserCreate
from dependencies.auth import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, user_usecase: UserUsecase = Depends(get_user_usecase)) -> UserOut:
    """
    사용자 정보 조회

    Args:
        user_id: 사용자 ID
        user_usecase: 의존성 주입된 UserUsecase

    Returns:
        UserOut: 사용자 정보

    Raises:
        HTTPException: 사용자를 찾을 수 없는 경우
    """
    user = user_usecase.get_user_profile(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"사용자를 찾을 수 없습니다. user_id: {user_id}"
        )

    return UserOut(**user.model_dump())


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, user_usecase: UserUsecase = Depends(get_user_usecase)) -> UserOut:

    """
    새 사용자 등록

    Args:
        user_data: 사용자 생성 데이터
        user_usecase: 의존성 주입된 UserUsecase

    Returns:
        UserOut: 생성된 사용자 정보

    Raises:
        HTTPException: 사용자 생성 실패 시
    """
    user = await user_usecase.register_user(

        email=user_data.email, password=user_data.password, timezone=user_data.timezone, language=user_data.language
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="사용자 생성에 실패했습니다.")

    return UserOut(**user.model_dump())


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user_id: int = Depends(get_current_user_id), user_usecase: UserUsecase = Depends(get_user_usecase)
) -> None:
    """
    현재 로그인한 사용자 삭제 (회원 탈퇴)
    """
    user_usecase.delete_user(current_user_id)
    return None
