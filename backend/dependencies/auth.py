# dependencies/auth.py
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import logging
from repo import get_user_repo
from clients import get_supabase_client

logger = logging.getLogger(__name__)

auth_scheme = HTTPBearer()


def get_current_user_id(authorization: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    """
    Authorization 헤더에서 JWT 토큰을 추출하고 검증하여 user_id 반환

    Args:
        authorization: Bearer {jwt_token} 형태의 헤더

    Returns:
        int: 검증된 사용자 ID (DB의 실제 user.id)

    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자가 존재하지 않는 경우
    """
    try:
        # 1. Bearer 토큰 추출
        scheme, token = authorization.scheme, authorization.credentials
        if not scheme == "Bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

        # 2. Supabase JWT 검증 및 UUID 추출
        logger.info(f"토큰 검증 시도: {token[:20]}...")
        supabase_client = get_supabase_client()
        response = supabase_client.auth.get_user(token)

        if not response or not response.user:
            logger.error(f"Supabase 토큰 검증 실패: response={response}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_uuid = response.user.id
        logger.info(f"JWT에서 추출한 사용자 UUID: {user_uuid}")

        if not user_uuid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing user UUID")

        # 3. UUID로 실제 DB의 user_id 조회
        user_repo = get_user_repo()
        logger.info(f"DB에서 UUID 조회 시도: {user_uuid}")
        user = user_repo.get_by_uuid(user_uuid)

        if not user:
            logger.error(f"Use not found from uuid: UUID={user_uuid}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        # 4. 이메일 인증 상태 확인 및 자동 업데이트
        supabase_email_confirmed = response.user.email_confirmed_at is not None
        logger.info(
            f"Supabase 이메일 확인 상태: {supabase_email_confirmed}, DB 이메일 확인 상태: {user.email_verified}"
        )

        if supabase_email_confirmed and not user.email_verified:
            # Supabase에서는 이메일 확인됐는데 DB에서는 미확인 상태인 경우 → 자동 업데이트
            logger.info(f"이메일 인증 완료 감지 - 자동 업데이트 실행: user_id={user.id}")
            update_success = user_repo.update_email_verified(user.id, True)
            if update_success:
                logger.info(f"이메일 인증 상태 자동 업데이트 성공: user_id={user.id}")
                user.email_verified = True  # 메모리상 객체도 업데이트
            else:
                logger.warning(f"이메일 인증 상태 자동 업데이트 실패: user_id={user.id}")

        elif not supabase_email_confirmed:
            # Supabase에서도 이메일 미확인 상태인 경우
            logger.warning(f"이메일 미인증 사용자 접근 시도: user_id={user.id}, email={user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="EMAIL_NOT_VERIFIED",  # 프론트엔드에서 구분할 수 있는 특별한 메시지
            )

        logger.info(f"인증 성공: UUID={user_uuid}, user_id={user.id}, email_verified={user.email_verified}")
        return user.id

    except ValueError as e:
        # user_repo.get_by_uuid()에서 발생하는 ValueError 처리
        logger.error(f"사용자 조회 실패: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    except Exception as e:
        logger.error(f"인증 실패: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")
