from typing import Optional
from data.schemas import PortfolioCreate, UserCreate, UserOut
from repo import UserRepo, PortfolioRepo
from data.models import User
from supabase import Client
import asyncio

import logging

logger = logging.getLogger(__name__)


class EmailNotVerifiedException(Exception):
    """이메일 미인증 예외"""

    pass



class UserUsecase:
    """
    사용자 관련 비즈니스 로직을 처리하는 UseCase 클래스
    Repository 패턴을 사용하여 데이터 접근을 캡슐화합니다.
    """

    def __init__(self, user_repo: UserRepo, portfolio_repo: PortfolioRepo, supabase_client: Client):

        """
        UserUsecase 초기화

        Args:
            user_repo: UserRepo 인스턴스 (의존성 주입용)
        """
        self.user_repo = user_repo
        self.portfolio_repo = portfolio_repo
        self.supabase_client = supabase_client


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
            user = self.user_repo.get_by_id(user_id)

            if not user:
                logger.warning(f"사용자를 찾을 수 없습니다. user_id: {user_id}")
                return None

            # 마지막 로그인 시간 업데이트
            self.user_repo.update_last_login(user_id)

            return user

        except Exception as e:
            logger.error(f"사용자 프로필 조회 실패: {e}")
            return None

    def get_user_profile_sync(self, user_id: int) -> Optional[User]:
        # 사용자 조회 (동기식으로 간단하게 처리)
        try:
            # 새로운 이벤트 루프 생성하여 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                user = loop.run_until_complete(self.user_repo.get_by_id(user_id))
            finally:
                loop.close()

            if not user:
                logger.warning(f"사용자를 찾을 수 없습니다. user_id: {user_id}")
                return None

            logger.info(f"사용자 조회 성공: user_id={user.id}, email={user.email}")

        except Exception as e:
            logger.error(f"사용자 프로필 조회 실패: {e}")
            return None

        # 로그인 시간 업데이트
        try:
            self.user_repo.update_last_login(user_id)
        except Exception as update_error:
            logger.warning(f"로그인 시간 업데이트 실패 (user_id: {user_id}): {update_error}")
        return user

    async def register_user(
        self, email: str, password: str, timezone: str = "UTC", language: str = "ko"
    ) -> Optional[User]:

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
            user = self.user_repo.create(
                schema=UserCreate(
                    email=email,
                    password=password,
                    timezone=timezone,
                    language=language,
                )
            )

            if not user:
                logger.error(f"사용자 생성 실패 (email: {email}): user_repo.create returned None")
                return None

            logger.info(f"새 사용자가 등록되었습니다. user_id: {user.id}, email: {email}")

            # Create User Portfolio
            try:
                portfolio = await self.portfolio_repo.create(schema=PortfolioCreate(user_id=user.id))
                if portfolio:
                    logger.info(f"사용자 포트폴리오 생성 완료: user_id={user.id}, portfolio_id={portfolio.id}")
                else:
                    logger.warning(f"포트폴리오 생성 실패: user_id={user.id} - portfolio_repo.create returned None")
            except Exception as portfolio_error:
                logger.error(f"포트폴리오 생성 중 오류 발생: user_id={user.id}, error={portfolio_error}")
                # 포트폴리오 생성 실패해도 사용자는 반환 (나중에 수동으로 생성 가능)


            return user

        except Exception as e:
            logger.error(f"사용자 등록 실패 (email: {email}): {e}")
            return None

    def _authenticate_with_supabase(self, email: str, password: str):
        """Supabase 인증 처리"""
        try:
            return self.supabase_client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as error:
            error_msg = str(error)
            logger.error(f"Supabase 인증 실패 (email: {email}): {error_msg}")

            if "Email not confirmed" in error_msg:
                raise EmailNotVerifiedException("이메일 확인이 필요합니다. 가입 시 받은 이메일을 확인해주세요.")

            raise  # 다른 오류는 그대로 재발생

    def _build_user_response(self, user, auth_response) -> UserOut:
        """사용자 응답 데이터 구성"""
        user_data = user.model_dump()

        if auth_response.session:
            user_data.update(
                {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "token_type": "Bearer",
                    "expires_in": getattr(auth_response.session, "expires_in", None),
                }
            )

        return UserOut(**user_data)

    def login(self, email: str, password: str) -> Optional[UserOut]:

        """
        사용자 로그인

        Args:
            email: 사용자 이메일
            password: 사용자 비밀번호

        Returns:
            UserOut | None: 사용자 정보 + 인증 토큰 정보 (로그인 실패 시 None)
        """
        try:
            # 1. Supabase 인증
            auth_response = self._authenticate_with_supabase(email, password)
            if not auth_response.user:
                logger.error(f"Supabase 인증 실패: 사용자 정보 없음 (email: {email})")
                raise Exception("계정 정보를 찾을 수 없습니다. 고객센터에 문의해주세요.")
        except Exception as e:
            logger.error(f"Supabase 인증 실패: {e}")
            raise e

        try:
            # 2. DB에서 사용자 정보 조회
            user_uuid = auth_response.user.id
            user = self.user_repo.get_by_uuid(user_uuid)

            if not user:
                logger.error(f"DB에 사용자 정보 없음: UUID={user_uuid}")
                raise Exception("계정 정보를 찾을 수 없습니다. 고객센터에 문의해주세요.")

            # 3. 로그인 시간 업데이트
            success = self.user_repo.update_last_login(user.id)
            if not success:
                logger.error(f"로그인 시간 업데이트 실패: user_id={user.id}")
                raise Exception("로그인 시간 업데이트 실패. 고객센터에 문의해주세요.")

            # 4. 응답 데이터 구성
            return self._build_user_response(user, auth_response)

        except EmailNotVerifiedException:
            logger.warning(f"이메일 미인증 로그인 시도 (email: {email})")
            raise
        except Exception as e:
            logger.error(f"로그인 처리 실패 (email: {email}): {e}")
            return None

    def sign_out(self):
        """
        사용자 로그아웃
        """
        try:
            self.supabase_client.auth.sign_out()
        except Exception as e:
            logger.error(f"사용자 로그아웃 실패: {e}")

    def delete_user(self, user_id: int):
        """
        사용자 삭제
        """
        try:
            _ = self.user_repo.delete_by_id(user_id)
        except Exception as e:
            logger.error(f"사용자 삭제 실패 (user_id: {user_id}): {e}")

    def resend_verification_email(self, email: str):
        """
        이메일 인증 메일 재발송
        """
        try:
            _ = self.supabase_client.auth.resend(
                {
                    "type": "signup",
                    "email": email,
                    "options": {
                        "email_redirect_to": "https://example.com/welcome",
                    },
                }
            )
        except Exception as e:
            logger.error(f"이메일 인증 메일 재발송 실패 (email: {email}): {e}")
            raise
