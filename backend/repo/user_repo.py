from typing import Optional
from supabase import Client
from data.models import User
import logging
from .base_repo import BaseRepo
from data.schemas import UserCreate, UserOut, UserPatch


logger = logging.getLogger(__name__)


class UserRepo(BaseRepo):
    """
    사용자 관련 데이터 접근 계층
    Supabase를 통한 사용자 정보 관리를 담당합니다.
    """

    def __init__(self, db_client: Client, table_name: str = "users"):
        super().__init__(db_client, table_name)

    def create(self, schema: UserCreate) -> Optional[UserOut]:
        """
        새 사용자 생성
        트리거를 활용하여 auth.users와 public.users를 자동으로 연동합니다.

        Args:
            schema: UserCreate

        Returns:
            User | None: 생성된 사용자 정보 또는 None
        """
        try:
            # 1. Supabase Auth에 사용자 생성 (동기 방식)
            basic_user = self.db_client.auth.sign_up(
                {
                    "email": schema.email,
                    "password": schema.password,
                    "options": {
                        "email_redirect_to": "https://porta-rose.vercel.app/",
                    },
                }
            )
            logger.info(f"Supabase 기본 사용자 생성 결과: {basic_user}")

            # 2. 사용자 정보 업데이트 (회원가입 시 이메일 인증 상태는 false)
            response = (
                self.db_client.table(self.table_name)
                .insert(
                    {
                        "uuid": basic_user.user.id,
                        "email": schema.email,
                        "timezone": schema.timezone,
                        "language": schema.language,
                        "email_verified": False,  # 회원가입 시 이메일 미인증 상태
                    }
                )
                .execute()
            )

            # 3. 업데이트된 사용자 정보 조회 및 반환
            if response.data and len(response.data) > 0:
                data = response.data[0]
                return UserOut(
                    id=data["id"],
                    uuid=data["uuid"],
                    email=data["email"],
                    timezone=data["timezone"],
                    language=data["language"],
                    email_verified=data.get("email_verified", False),
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    last_login=data.get("last_login"),
                    access_token=basic_user.session.access_token if basic_user.session else None,
                    refresh_token=basic_user.session.refresh_token if basic_user.session else None,
                    token_type="Bearer" if basic_user.session else None,
                    expires_in=basic_user.session.expires_in if basic_user.session else None,
                )
            return None

        except Exception as e:
            logger.error(f"사용자 생성 실패 (email: {schema.email}): {e}")
            return None

    def get_by_id(self, id: int) -> Optional[User]:
        """
        DB에서 사용자 정보 조회

        Args:
            id: user ID

        Returns:
            User | None: 사용자 정보 또는 None
        """
        try:
            response = self.db_client.table(self.table_name).select("*").eq("id", id).single().execute()

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
            logger.error(f"사용자 정보 조회 실패 (id: {id}): {e}")
            return None

    def get_by_uuid(self, uuid: str) -> Optional[UserOut]:
        try:
            logger.debug(f"DB에서 사용자 조회 시도: UUID={uuid}")
            response = self.db_client.table(self.table_name).select("*").eq("uuid", uuid).single().execute()
            data = response.data

            if data:
                logger.debug(f"사용자 조회 성공: UUID={uuid}, DB_ID={data['id']}")
                return UserOut(
                    id=data["id"],
                    email=data["email"],
                    timezone=data["timezone"],
                    language=data["language"],
                    email_verified=data.get("email_verified", False),
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    last_login=data.get("last_login"),
                )
            else:
                logger.warning(f"사용자를 찾을 수 없습니다. UUID: {uuid}")
                return None

        except Exception as e:
            logger.error(f"사용자 정보 조회 실패 (uuid: {uuid}): {e}")
            return None

    def update(self, schema: UserPatch) -> UserOut:
        """
        사용자 정보 업데이트

        Args:
            schema: UserPatch

        Returns:
            User: 업데이트된 사용자 정보
        """
        try:
            response = self.db_client.table(self.table_name).update(schema.model_dump()).eq("id", schema.id).execute()
            if response.data and len(response.data) > 0:
                data = response.data
                return UserOut(
                    id=data["id"],
                    email=data["email"],
                    timezone=data["timezone"],
                    language=data["language"],
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    last_login=data.get("last_login"),
                )
        except Exception as e:
            logger.error(f"사용자 정보 업데이트 실패 (id: {schema.id}): {e}")

    def delete_by_id(self, id: int) -> bool:
        """
        사용자 정보 삭제
        """
        try:
            # get user from id
            user = self.get_by_id(id)
            if not user:
                raise ValueError(f"사용자를 찾을 수 없습니다. id: {id}")

            # delete public.users
            response = self.db_client.table(self.table_name).delete().eq("id", id).execute()

            # delete auth.users
            self.db_client.auth.admin.delete_user(user.uuid, should_soft_delete=True)

            return len(response.data) > 0
        except Exception as e:
            logger.error(f"사용자 정보 삭제 실패 (id: {id}): {e}")
            return False

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

    def update_email_verified(self, user_id: int, verified: bool = True) -> bool:
        """
        사용자의 이메일 인증 상태 업데이트

        Args:
            user_id: 사용자 ID
            verified: 인증 상태 (기본값: True)

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            logger.debug(f"이메일 인증 상태 업데이트: user_id={user_id}, verified={verified}")
            response = (
                self.db_client.table(self.table_name).update({"email_verified": verified}).eq("id", user_id).execute()
            )

            success = len(response.data) > 0
            if success:
                logger.info(f"이메일 인증 상태 업데이트 성공: user_id={user_id}, verified={verified}")
            else:
                logger.warning(f"이메일 인증 상태 업데이트 실패: user_id={user_id} (사용자를 찾을 수 없음)")

            return success

        except Exception as e:
            logger.error(f"이메일 인증 상태 업데이트 실패 (user_id: {user_id}): {e}")
            return False
