from fastapi import APIRouter, Depends, HTTPException, status
from usecase import UserUsecase, get_user_usecase
from data.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(email: str, password: str, user_usecase: UserUsecase = Depends(get_user_usecase)) -> UserOut:
    user = user_usecase.login(email=email, password=password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="로그인에 실패했습니다.")
    return UserOut(**user.model_dump())
