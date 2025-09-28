from typing import Optional
from repo import UserRepo, get_user_repo
from data.models import User
import logging

logger = logging.getLogger(__name__)


class UserUsecase:
    """
    사용자 관련 비즈니스 로직을 처리하는 UseCase 클래스
    Repository 패턴을 사용하여 데이터 접근을 캡슐화합니다.
    """

    def __init__(self, user_repo: Optional[UserRepo] = None):
        """
        UserUsecase 초기화

        Args:
            user_repo: UserRepo 인스턴스 (의존성 주입용)
        """
        self.user_repo = user_repo or get_user_repo()

    def get_user_profile(self, user_id: int) -> Optional[User]:
        """
        사용자 프로필 정보를 조회하고 마지막 로그인 시간을 업데이트합니다.

        Args:
            user_id: 사용자 ID

        Returns:
            User | None: 사용자 정보
        """
        try:
            # 사용자 정보 조회
            user = self.user_repo.get_user_info(user_id)
            if not user:
                logger.warning(f"사용자를 찾을 수 없습니다. user_id: {user_id}")
                return None

            # 마지막 로그인 시간 업데이트
            self.user_repo.update_last_login(user_id)

            return user

        except Exception as e:
            logger.error(f"사용자 프로필 조회 실패: {e}")
            return None

    def register_user(self, email: str, password: str, timezone: str = "UTC", language: str = "ko") -> Optional[User]:
        """
        새 사용자를 등록합니다.

        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호
            timezone: 시간대
            language: 언어

        Returns:
            User | None: 생성된 사용자 정보
        """
        try:
            # TODO: 이메일 중복 확인 로직 추가

            # Create user
            user = self.user_repo.create_user(email, password, timezone, language)
            if user:
                logger.info(f"새 사용자가 등록되었습니다. user_id: {user.id}, email: {email}")

            return user

        except Exception as e:
            logger.error(f"사용자 등록 실패 (email: {email}): {e}")
            return None

    def login(self, email: str, password: str) -> Optional[User]:
        """
        사용자 로그인

        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호

        Returns:
            User | None: 로그인된 사용자 정보
        """
        try:
            return self.user_repo.login(email, password)
        except Exception as e:
            logger.error(f"사용자 로그인 실패 (email: {email}): {e}")
            return None
