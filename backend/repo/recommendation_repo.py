# repo/recommendation_repo.py
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from supabase import Client

from data.schemas import RecommendationCreate, RecommendationOut, RecommendationReturnsPatch
from .base_repo import BaseRepo
import logging

logger = logging.getLogger(__name__)


class RecommendationRepo(BaseRepo):
    """추천 트랙레코드 저장소"""

    def __init__(self, db_client: Client, table_name: str = "recommendations"):
        super().__init__(db_client, table_name)

    async def create(self, schema: RecommendationCreate) -> RecommendationOut:
        """추천 1건 기록"""
        results = await self.create_many([schema])
        return results[0]

    async def create_many(self, schemas: List[RecommendationCreate]) -> List[RecommendationOut]:
        """추천 일괄 기록 (런당 1회)"""
        if not schemas:
            return []
        try:
            rows = [schema.model_dump(mode="json") for schema in schemas]
            response = self.db_client.table(self.table_name).insert(rows).execute()
            if not response.data:
                raise ValueError("추천 기록 실패: 응답 데이터가 없습니다")
            return [RecommendationOut(**row) for row in response.data]
        except Exception as e:
            logger.error(f"추천 기록 중 예외 발생: {e}")
            raise e

    async def get_by_id(self, id: int) -> Optional[RecommendationOut]:
        """ID로 추천 조회"""
        try:
            response = self.db_client.table(self.table_name).select("*").eq("id", id).execute()
            if response.data:
                return RecommendationOut(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"추천 조회 중 예외 발생: {e}")
            raise e

    async def get_recent(self, user_id: int, days: int = 120) -> List[RecommendationOut]:
        """최근 N일간의 추천 조회 (채점/스코어카드용)"""
        try:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            response = (
                self.db_client.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", since)
                .order("created_at", desc=True)
                .execute()
            )
            return [RecommendationOut(**row) for row in response.data or []]
        except Exception as e:
            logger.error(f"최근 추천 조회 중 예외 발생: {e}")
            raise e

    async def update(self, id: int, schema: RecommendationReturnsPatch) -> Optional[RecommendationOut]:
        """채점 결과 갱신 (null 필드는 건드리지 않음)"""
        try:
            patch = schema.model_dump(mode="json", exclude_none=True)
            if not patch:
                return await self.get_by_id(id)
            response = self.db_client.table(self.table_name).update(patch).eq("id", id).execute()
            if response.data:
                return RecommendationOut(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"추천 채점 갱신 중 예외 발생: {e}")
            raise e

    async def delete_by_id(self, id: int) -> bool:
        """추천 삭제"""
        try:
            response = self.db_client.table(self.table_name).delete().eq("id", id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"추천 삭제 중 예외 발생: {e}")
            raise e
