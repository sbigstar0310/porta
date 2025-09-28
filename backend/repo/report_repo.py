from typing import List, Optional
from data.schemas import ReportOut, ReportCreate, ReportPatch
from supabase import Client
from dateutil import parser as date_parser
from .base_repo import BaseRepo
import logging

logger = logging.getLogger(__name__)


class ReportRepo(BaseRepo):
    def __init__(self, db_client: Client, table_name: str = "reports"):
        super().__init__(db_client, table_name)

    async def create(self, schema: ReportCreate) -> ReportOut:
        """
        보고서 생성

        Args:
            schema: 보고서 생성 스키마

        Returns:
            ReportOut: 생성된 보고서 정보
        """
        try:
            response = self.db_client.table(self.table_name).insert(schema.model_dump(mode="json")).execute()
            if response.data:
                return ReportOut(**response.data[0])
            else:
                logger.error(f"보고서 생성 실패: 응답 데이터가 없습니다. response: {response}")
                raise ValueError("보고서 생성 실패: 응답 데이터가 없습니다")
        except Exception as e:
            logger.error(f"보고서 생성 중 예외 발생: {e}")
            raise e

    async def get_by_id(self, report_id: int) -> Optional[ReportOut]:
        """
        ID로 보고서 조회

        Args:
            report_id: 보고서 ID

        Returns:
            Optional[ReportOut]: 보고서 정보
        """
        try:
            response = self.db_client.table(self.table_name).select("*").eq("id", report_id).single().execute()
            if response.data:
                data = response.data
                # datetime 파싱 처리
                data["created_at"] = date_parser.parse(data["created_at"])
                return ReportOut(**data)
            return None
        except Exception as e:
            logger.error(f"보고서 조회 중 예외 발생 (ID: {report_id}): {e}")
            return None

    async def get_by_user_id(
        self, user_id: int, limit: int = 20, offset: int = 0, order_by: str = "created_at", desc: bool = True
    ) -> List[ReportOut]:
        """
        사용자별 보고서 목록 조회 (페이지네이션 지원)

        Args:
            user_id: 사용자 ID
            limit: 한 번에 가져올 개수 (기본 20)
            offset: 건너뛸 개수 (기본 0)
            order_by: 정렬 기준 필드 (기본 created_at)
            desc: 내림차순 여부 (기본 True)

        Returns:
            List[ReportOut]: 보고서 목록
        """
        try:
            query = (
                self.db_client.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .range(offset, offset + limit - 1)
            )

            # 정렬 적용
            if desc:
                query = query.order(order_by, desc=True)
            else:
                query = query.order(order_by)

            response = query.execute()

            if response.data:
                reports = []
                for data in response.data:
                    # datetime 파싱 처리
                    data["created_at"] = date_parser.parse(data["created_at"])
                    reports.append(ReportOut(**data))
                return reports
            return []
        except Exception as e:
            logger.error(f"사용자별 보고서 목록 조회 중 예외 발생 (user_id: {user_id}): {e}")
            return []

    async def get_latest_by_user_id(self, user_id: int) -> Optional[ReportOut]:
        """
        사용자의 최신 보고서 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[ReportOut]: 최신 보고서 정보
        """
        try:
            response = (
                self.db_client.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .single()
                .execute()
            )
            if response.data:
                data = response.data
                # datetime 파싱 처리
                data["created_at"] = date_parser.parse(data["created_at"])
                return ReportOut(**data)
            return None
        except Exception as e:
            logger.error(f"최신 보고서 조회 중 예외 발생 (user_id: {user_id}): {e}")
            return None

    async def update(self, report_id: int, schema: ReportPatch) -> Optional[ReportOut]:
        """
        보고서 정보 업데이트

        Args:
            report_id: 보고서 ID
            schema: 보고서 수정 스키마

        Returns:
            Optional[ReportOut]: 업데이트된 보고서 정보
        """
        try:
            response = (
                self.db_client.table(self.table_name)
                .update(schema.model_dump(mode="json", exclude_none=True))
                .eq("id", report_id)
                .single()
                .execute()
            )
            if response.data:
                data = response.data
                # datetime 파싱 처리
                data["created_at"] = date_parser.parse(data["created_at"])
                return ReportOut(**data)
            return None
        except Exception as e:
            logger.error(f"보고서 업데이트 중 예외 발생 (ID: {report_id}): {e}")
            raise e

    async def delete_by_id(self, report_id: int) -> bool:
        """
        보고서 삭제

        Args:
            report_id: 보고서 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            response = self.db_client.table(self.table_name).delete().eq("id", report_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"보고서 삭제 중 예외 발생 (ID: {report_id}): {e}")
            raise e

    async def count_by_user_id(self, user_id: int) -> int:
        """
        사용자별 보고서 총 개수 조회

        Args:
            user_id: 사용자 ID

        Returns:
            int: 보고서 총 개수
        """
        try:
            response = (
                self.db_client.table(self.table_name).select("id", count="exact").eq("user_id", user_id).execute()
            )
            return response.count or 0
        except Exception as e:
            logger.error(f"보고서 개수 조회 중 예외 발생 (user_id: {user_id}): {e}")
            return 0
