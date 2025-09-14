from typing import Optional
from supabase import Client
from data.models import User
import logging

logger = logging.getLogger(__name__)


class UserRepo:
    """
    사용자 관련 데이터 접근 계층
    Supabase를 통한 사용자 정보 관리를 담당합니다.
    """

    def __init__(self, db_client: Optional[Client] = None):
        """
        UserRepo 초기화

        Args:
            db_client: Supabase 클라이언트 (의존성 주입용, 없으면 자동으로 가져옴)
        """
        self.db_client = db_client

    def get_user_info(self, user_id: int = 1) -> Optional[User]:
        """
        DB에서 사용자 정보 조회

        Args:
            user_id: 사용자 ID

        Returns:
            User | None: 사용자 정보 또는 None
        """
        try:
            response = self.db_client.table("users").select("*").eq("id", user_id).single().execute()

            if response.data:
                data = response.data
                return User(
                    id=data["id"],
                    uuid=data.get("uuid"),
                    email=data["email"],
                    timezone=data.get("timezone"),
                    language=data.get("language"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    last_login=data.get("last_login"),
                )
            return None

        except Exception as e:
            logger.error(f"사용자 정보 조회 실패 (user_id: {user_id}): {e}")
            return None

    def create_user(self, email: str, password: str, timezone: str = "UTC", language: str = "ko") -> Optional[User]:
        """
        새 사용자 생성
        트리거를 활용하여 auth.users와 public.users를 자동으로 연동합니다.

        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호
            timezone: 시간대 (기본: UTC)
            language: 언어 (기본: ko)

        Returns:
            User | None: 생성된 사용자 정보 또는 None
        """
        try:
            # 1. Supabase Auth에 사용자 생성 (동기 방식)
            basic_user = self.db_client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )
            logger.info(f"Supabase 기본 사용자 생성 결과: {basic_user}")

            # 2. 사용자 정보 업데이트
            user_uuid = basic_user.user.id
            response = (
                self.db_client.table("users")
                .insert(
                    {
                        "uuid": user_uuid,
                        "email": email,
                        "timezone": timezone,
                        "language": language,
                    }
                )
                .execute()
            )

            # 3. 업데이트된 사용자 정보 조회 및 반환
            if response.data and len(response.data) > 0:
                data = response.data[0]
                return User(
                    id=data["id"],
                    uuid=data["uuid"],
                    email=data["email"],
                    timezone=data["timezone"],
                    language=data["language"],
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    last_login=data.get("last_login"),
                )
            return None

        except Exception as e:
            logger.error(f"사용자 생성 실패 (email: {email}): {e}")
            return None

    def update_last_login(self, user_id: int) -> bool:
        """
        사용자 마지막 로그인 시간 업데이트

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            response = self.db_client.table("users").update({"last_login": "NOW()"}).eq("id", user_id).execute()

            return len(response.data) > 0

        except Exception as e:
            logger.error(f"마지막 로그인 시간 업데이트 실패 (user_id: {user_id}): {e}")
            return False

    def login(self, email: str, password: str) -> Optional[User]:
        """
        사용자 로그인

        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호

        Returns:
            User | None: 로그인된 사용자 정보 또는 None
        """
        try:
            # Supabase Auth 로그인 (딕셔너리 형태로 전달)
            auth_response = self.db_client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            logger.info(f"로그인 응답: {auth_response}")

            # 로그인 성공 시 사용자 정보 조회
            user_uuid = auth_response.user.id
            response = self.db_client.table("users").select("*").eq("uuid", user_uuid).single().execute()

            if response.data:
                data = response.data
                user = User(
                    id=data["id"],
                    uuid=data["uuid"],
                    email=data["email"],
                    timezone=data.get("timezone", "UTC"),
                    language=data.get("language", "ko"),
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    last_login=data.get("last_login"),
                )

                # 마지막 로그인 시간 업데이트
                self.update_last_login(user.id)

                return user

            return None

        except Exception as e:
            logger.error(f"사용자 로그인 실패 (email: {email}): {e}")
            return None
