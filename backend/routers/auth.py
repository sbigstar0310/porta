from fastapi import APIRouter, Depends, HTTPException, status, Form
from usecase import UserUsecase, get_user_usecase
from usecase.user_usecase import EmailNotVerifiedException
from data.schemas import UserOut
import logging

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


@router.post("/login")
def login(
    email: str = Form(..., description="사용자 이메일"),
    password: str = Form(..., description="사용자 비밀번호"),
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> UserOut:
    try:
        user = user_usecase.login(email=email, password=password)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="로그인에 실패했습니다.")
        return user
    except EmailNotVerifiedException as e:
        logger.warning(f"이메일 미인증 로그인 시도 (email: {email}): {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="EMAIL_NOT_VERIFIED")
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error logging in: {e}")


@router.post("/signout")
def signout(
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> dict:
    try:
        user_usecase.sign_out()
        return {"message": "로그아웃 되었습니다."}
    except Exception as e:
        logger.error(f"Error signing out: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error signing out: {e}")


@router.post("/resend-verification-email")
def resend_verification_email(
    email: str = Form(..., description="사용자 이메일"),
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> dict:
    try:
        user_usecase.resend_verification_email(email=email)
        return {"message": "이메일 인증 메일이 발송되었습니다."}
    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error resending verification email: {e}"
        )


@router.post("/refresh")
def refresh_token(
    refresh_token: str = Form(..., description="refresh token"),
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> UserOut:
    try:
        user = user_usecase.refresh_session(refresh_token=refresh_token)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="리프레시 세션 갱신에 실패했습니다.")
        return user
    except Exception as e:
        logger.error(f"Error refreshing session: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error refreshing session: {e}")
