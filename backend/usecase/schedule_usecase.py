from typing import Optional, List
from repo.schedule_repo import ScheduleRepo
from data.schemas import ScheduleOut, ScheduleCreate, SchedulePatch
import logging

logger = logging.getLogger(__name__)


class ScheduleAlreadyExistsException(Exception):
    """스케줄 중복 생성 예외"""

    pass


class ScheduleNotFoundOrUnauthorizedException(Exception):
    """스케줄을 찾을 수 없거나 권한이 없는 예외"""

    pass


class ScheduleUsecase:
    def __init__(self, schedule_repo: ScheduleRepo):
        """
        ScheduleUsecase 초기화

        Args:
            schedule_repo: ScheduleRepo 인스턴스 (의존성 주입용)
        """
        self.schedule_repo = schedule_repo

    async def create_schedule(
        self,
        user_id: int,
        hour: int,
        minute: int,
        timezone: str = "Asia/Seoul",
        enabled: bool = True,
    ) -> ScheduleOut:
        """
        새로운 스케줄 생성 (사용자당 하나의 스케줄만 허용)

        Args:
            user_id: 사용자 ID
            hour: 시간 (0-23)
            minute: 분 (0-59)
            timezone: 시간대 (기본: Asia/Seoul)
            enabled: 활성화 여부 (기본: True)

        Returns:
            ScheduleOut: 생성된 스케줄 정보

        Raises:
            ScheduleAlreadyExistsException: 이미 스케줄이 존재하는 경우
        """
        try:
            # 기존 스케줄 존재 여부 확인
            existing_schedules = await self.schedule_repo.get_by_user_id(user_id)
            if existing_schedules:
                logger.warning(f"사용자 스케줄 중복 생성 시도: user_id={user_id}")
                raise ScheduleAlreadyExistsException("이미 스케줄이 존재합니다. 하나의 스케줄만 생성할 수 있습니다.")

            # 새 스케줄 생성
            result = await self.schedule_repo.create(
                ScheduleCreate(
                    user_id=user_id,
                    hour=hour,
                    minute=minute,
                    timezone=timezone,
                    enabled=enabled,
                )
            )
            logger.info(f"스케줄 생성 완료: user_id={user_id}, schedule_id={result.id}, time={hour:02d}:{minute:02d}")
            return result

        except ScheduleAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"스케줄 생성 실패: user_id={user_id}, error={e}")
            raise e

    async def get_user_schedule(self, user_id: int) -> Optional[ScheduleOut]:
        """
        사용자의 스케줄 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[ScheduleOut]: 사용자의 스케줄 정보 (없으면 None)
        """
        try:
            schedule = await self.schedule_repo.get_by_user_id(user_id)
            if schedule:
                # 사용자당 하나의 스케줄만 있어야 하므로 첫 번째 스케줄 반환
                logger.info(f"사용자 스케줄 조회 완료: user_id={user_id}, schedule_id={schedule.id}")
                return schedule

            logger.info(f"사용자 스케줄 없음: user_id={user_id}")
            return None

        except Exception as e:
            logger.error(f"사용자 스케줄 조회 실패: user_id={user_id}, error={e}")
            raise e

    async def get_schedule_by_id(self, schedule_id: int, user_id: int) -> Optional[ScheduleOut]:
        """
        스케줄 ID로 조회 (권한 확인 포함)

        Args:
            schedule_id: 스케줄 ID
            user_id: 요청한 사용자 ID (권한 확인용)

        Returns:
            Optional[ScheduleOut]: 스케줄 정보

        Raises:
            ScheduleNotFoundOrUnauthorizedException: 스케줄이 없거나 권한이 없는 경우
        """
        try:
            schedule = await self.schedule_repo.get_by_id(schedule_id)

            if not schedule:
                logger.warning(f"스케줄을 찾을 수 없습니다: schedule_id={schedule_id}")
                raise ScheduleNotFoundOrUnauthorizedException("스케줄을 찾을 수 없습니다.")

            # 권한 확인: 본인의 스케줄만 조회 가능
            if schedule.user_id != user_id:
                logger.warning(
                    f"스케줄 접근 권한 없음: schedule_id={schedule_id}, user_id={user_id}, owner_id={schedule.user_id}"
                )
                raise ScheduleNotFoundOrUnauthorizedException("해당 스케줄에 접근할 권한이 없습니다.")

            logger.info(f"스케줄 조회 완료: schedule_id={schedule_id}, user_id={user_id}")
            return schedule

        except ScheduleNotFoundOrUnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"스케줄 조회 실패: schedule_id={schedule_id}, user_id={user_id}, error={e}")
            raise e

    async def update_schedule(
        self,
        user_id: int,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        timezone: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[ScheduleOut]:
        """
        사용자의 스케줄 업데이트

        Args:
            user_id: 사용자 ID
            hour: 변경할 시간 (선택적)
            minute: 변경할 분 (선택적)
            timezone: 변경할 시간대 (선택적)
            enabled: 변경할 활성화 상태 (선택적)

        Returns:
            Optional[ScheduleOut]: 업데이트된 스케줄 정보

        Raises:
            ScheduleNotFoundOrUnauthorizedException: 스케줄이 없는 경우
        """
        try:
            # 기존 스케줄 조회
            existing_schedule = await self.get_user_schedule(user_id)
            if not existing_schedule:
                logger.warning(f"업데이트할 스케줄이 없습니다: user_id={user_id}")
                raise ScheduleNotFoundOrUnauthorizedException("업데이트할 스케줄이 없습니다.")

            # 업데이트할 데이터만 포함하는 스키마 생성
            update_data = {}
            if hour is not None:
                update_data["hour"] = hour
            if minute is not None:
                update_data["minute"] = minute
            if timezone is not None:
                update_data["timezone"] = timezone
            if enabled is not None:
                update_data["enabled"] = enabled

            if not update_data:
                logger.warning(f"업데이트할 데이터가 없습니다: user_id={user_id}")
                return existing_schedule

            schema = SchedulePatch(**update_data)
            result = await self.schedule_repo.update(existing_schedule.id, schema)

            if result:
                logger.info(f"스케줄 업데이트 완료: user_id={user_id}, schedule_id={existing_schedule.id}")
            return result

        except ScheduleNotFoundOrUnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"스케줄 업데이트 실패: user_id={user_id}, error={e}")
            raise e

    async def delete_schedule(self, user_id: int) -> bool:
        """
        사용자의 스케줄 삭제

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 삭제 성공 여부

        Raises:
            ScheduleNotFoundOrUnauthorizedException: 스케줄이 없는 경우
        """
        try:
            # 기존 스케줄 조회
            existing_schedule = await self.get_user_schedule(user_id)
            if not existing_schedule:
                logger.warning(f"삭제할 스케줄이 없습니다: user_id={user_id}")
                raise ScheduleNotFoundOrUnauthorizedException("삭제할 스케줄이 없습니다.")

            # 스케줄 삭제
            result = await self.schedule_repo.delete_by_id(existing_schedule.id)

            if result:
                logger.info(f"스케줄 삭제 완료: user_id={user_id}, schedule_id={existing_schedule.id}")
            return result

        except ScheduleNotFoundOrUnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"스케줄 삭제 실패: user_id={user_id}, error={e}")
            raise e

    async def toggle_schedule(self, user_id: int) -> Optional[ScheduleOut]:
        """
        사용자 스케줄의 활성화 상태 토글

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[ScheduleOut]: 업데이트된 스케줄 정보

        Raises:
            ScheduleNotFoundOrUnauthorizedException: 스케줄이 없는 경우
        """
        try:
            # 기존 스케줄 조회
            existing_schedule = await self.get_user_schedule(user_id)
            if not existing_schedule:
                logger.warning(f"토글할 스케줄이 없습니다: user_id={user_id}")
                raise ScheduleNotFoundOrUnauthorizedException("토글할 스케줄이 없습니다.")

            # 활성화 상태 토글
            new_enabled = not existing_schedule.enabled
            result = await self.update_schedule(user_id, enabled=new_enabled)

            if result:
                logger.info(f"스케줄 상태 토글 완료: user_id={user_id}, enabled={new_enabled}")
            return result

        except ScheduleNotFoundOrUnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"스케줄 상태 토글 실패: user_id={user_id}, error={e}")
            raise e

    # Celery Beat 관련 유틸리티 메서드들

    async def get_all_enabled_schedules(self) -> List[ScheduleOut]:
        """
        모든 활성화된 스케줄 조회 (Celery Beat용)

        Returns:
            List[ScheduleOut]: 활성화된 스케줄 목록
        """
        try:
            schedules = await self.schedule_repo.get_enabled_schedules()
            logger.info(f"활성화된 스케줄 조회 완료: count={len(schedules)}")
            return schedules

        except Exception as e:
            logger.error(f"활성화된 스케줄 조회 실패: error={e}")
            raise e

    async def has_user_schedule(self, user_id: int) -> bool:
        """
        사용자가 스케줄을 가지고 있는지 확인

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 스케줄 존재 여부
        """
        try:
            schedule = await self.get_user_schedule(user_id)
            return schedule is not None

        except Exception as e:
            logger.error(f"사용자 스케줄 존재 확인 실패: user_id={user_id}, error={e}")
            return False

    async def is_schedule_enabled(self, user_id: int) -> bool:
        """
        사용자 스케줄이 활성화되어 있는지 확인

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 스케줄 활성화 여부 (스케줄이 없으면 False)
        """
        try:
            schedule = await self.get_user_schedule(user_id)
            return schedule.enabled if schedule else False

        except Exception as e:
            logger.error(f"사용자 스케줄 활성화 상태 확인 실패: user_id={user_id}, error={e}")
            return False
