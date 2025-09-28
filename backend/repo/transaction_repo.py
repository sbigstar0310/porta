from typing import List
from datetime import datetime, timedelta
from supabase import Client
import logging

from data.schemas import TransactionOut, TransactionCreate
from data.models import Transaction
from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class TransactionRepo(BaseRepo):
    def __init__(self, db_client: Client, table_name: str = "transactions"):
        super().__init__(db_client, table_name)

    async def get_by_id(self, id: int, **kwargs) -> TransactionOut:
        response = self.db_client.table(self.table_name).select("*").eq("id", id).single().execute()
        if response.data:
            data = response.data
            return TransactionOut(**data)
        return None

    async def create(self, schema: TransactionCreate) -> TransactionOut:
        response = self.db_client.table(self.table_name).insert(schema.model_dump(mode="json")).execute()
        if response.data:
            data = response.data[0]
            return TransactionOut(**data)
        return None

    async def update(self, id: int, schema: TransactionCreate) -> TransactionOut:
        response = self.db_client.table(self.table_name).update(schema.model_dump(mode="json")).eq("id", id).execute()
        if response.data:
            data = response.data
            return TransactionOut(**data)
        return None

    async def delete_by_id(self, id: int) -> bool:
        response = self.db_client.table(self.table_name).delete().eq("id", id).execute()
        return len(response.data) > 0

    async def get_recent_transactions(self, portfolio_id: int = 1, days: int = 7) -> List[Transaction]:
        """DB에서 최근 거래 기록 조회"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()

            if not self.db_client:
                raise ValueError("DB client not initialized")

            response = (
                self.db_client.table(self.table_name)
                .select("*")
                .eq("portfolio_id", portfolio_id)
                .gte("transaction_date", cutoff_date)
                .order("transaction_date", desc=True)
                .execute()
            )
            if response.data:
                data = response.data
                return [Transaction(**row) for row in data]
            return []

        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return []
