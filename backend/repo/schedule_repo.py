from typing import List, Optional
from data.schemas import ScheduleOut, ScheduleCreate, SchedulePatch
from supabase import Client
from .base_repo import BaseRepo
import logging

logger = logging.getLogger(__name__)


class ScheduleRepo(BaseRepo):
    def __init__(self, db_client: Client, table_name: str = "schedules"):
        super().__init__(db_client, table_name)

    async def create(self, schema: ScheduleCreate, **kwargs) -> ScheduleOut:
        """
        스케줄 생성

        Args:
            schema: 스케줄 생성 스키마

        Returns:
            ScheduleOut: 생성된 스케줄 정보
        """
        try:
            response = self.db_client.table(self.table_name).insert(schema.model_dump(mode="json")).execute()
            if response.data:
                return ScheduleOut(**response.data[0])
            else:
                logger.error(f"스케줄 생성 실패: 응답 데이터가 없습니다. response: {response}")
                raise ValueError("스케줄 생성 실패: 응답 데이터가 없습니다")
        except Exception as e:
            logger.error(f"스케줄 생성 중 예외 발생: {e}")
            raise e

    async def get_by_id(self, id: int) -> Optional[ScheduleOut]:
        """
        ID로 스케줄 조회

        Args:
            id: 스케줄 ID

        Returns:
            Optional[ScheduleOut]: 스케줄 정보
        """
        try:
            response = self.db_client.table(self.table_name).select("*").eq("id", id).single().execute()
            if response.data:
                return ScheduleOut(**response.data)
            return None
        except Exception as e:
            logger.error(f"스케줄 조회 중 예외 발생 (ID: {id}): {e}")
            return None

    async def get_by_user_id(self, user_id: int) -> List[ScheduleOut]:
        """
        사용자별 스케줄 목록 조회

        Args:
            user_id: 사용자 ID

        Returns:
            List[ScheduleOut]: 스케줄 목록
        """
        try:
            response = (
                self.db_client.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("hour", desc=False)
                .order("minute", desc=False)
                .execute()
            )

            print(response.data)

            if response.data:
                return ScheduleOut(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"사용자별 스케줄 목록 조회 중 예외 발생 (user_id: {user_id}): {e}")
            return None

    async def get_enabled_schedules(self) -> List[ScheduleOut]:
        """
        활성화된 모든 스케줄 조회

        Returns:
            List[ScheduleOut]: 활성화된 스케줄 목록
        """
        try:
            response = (
                self.db_client.table(self.table_name)
                .select("*")
                .eq("enabled", True)
                .order("hour", desc=False)
                .order("minute", desc=False)
                .execute()
            )

            if response.data:
                return [ScheduleOut(**data) for data in response.data]
            return []
        except Exception as e:
            logger.error(f"활성화된 스케줄 조회 중 예외 발생: {e}")
            return []

    async def update(self, schedule_id: int, schema: SchedulePatch) -> Optional[ScheduleOut]:
        """
        스케줄 정보 업데이트

        Args:
            schedule_id: 스케줄 ID
            schema: 스케줄 수정 스키마

        Returns:
            Optional[ScheduleOut]: 업데이트된 스케줄 정보
        """
        try:
            response = (
                self.db_client.table(self.table_name)
                .update(schema.model_dump(mode="json", exclude_none=True))
                .eq("id", schedule_id)
                .execute()
            )
            if response.data:
                return ScheduleOut(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"스케줄 업데이트 중 예외 발생 (ID: {schedule_id}): {e}")
            raise e

    async def delete_by_id(self, id: int) -> bool:
        """
        스케줄 삭제

        Args:
            id: 스케줄 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            response = self.db_client.table(self.table_name).delete().eq("id", id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"스케줄 삭제 중 예외 발생 (ID: {id}): {e}")
            raise e

    async def delete_by_user_id(self, user_id: int) -> bool:
        """
        사용자의 모든 스케줄 삭제

        Args:
            user_id: 사용자 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            _ = self.db_client.table(self.table_name).delete().eq("user_id", user_id).execute()
            return True  # 삭제할 데이터가 없어도 성공으로 간주
        except Exception as e:
            logger.error(f"사용자 스케줄 삭제 중 예외 발생 (user_id: {user_id}): {e}")
            raise e
