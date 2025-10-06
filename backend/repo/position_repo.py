from data.models import Position
from .base_repo import BaseRepo
from supabase import Client
from data.schemas import PositionCreate, PositionOut, PositionPatch
from typing import Optional
from clients.stock_client import StockClient
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PositionRepo(BaseRepo):
    def __init__(self, db_client: Client, stock_client: StockClient, table_name: str = "positions"):
        super().__init__(db_client, table_name)
        self.stock_client = stock_client

    def _get_enriched_position(self, position: Position) -> PositionOut:
        """포지션별 실시간 계산 필드들 계산 (현재가, 시장가치, 미실현 손익, 미실현 손익 비율)

        Args:
            position: 포지션 모델

        Returns:
            PositionOut: 포지션 출력 모델
        """
        try:
            ticker = position.ticker
            current_price = self.stock_client.get_stock_current_price([ticker])[ticker]
            if not current_price:
                raise ValueError(f"Current price not found for ticker: {ticker}")
            total_shares = float(position.total_shares)
            avg_buy_price = float(position.avg_buy_price)

            market_value = total_shares * current_price
            cost_basis = total_shares * avg_buy_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else Decimal("0.00")

            return PositionOut(
                **position.model_dump(),
                current_price=current_price,
                current_market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
            )
        except Exception as e:
            logger.error(f"Error getting enriched position: {e}")
            raise e

    async def create(self, position: PositionCreate) -> Optional[PositionOut]:
        try:
            # mode='json'을 사용하여 Decimal을 자동으로 JSON 호환 타입으로 변환
            position_data = position.model_dump(mode="json")
            response = self.db_client.table(self.table_name).insert(position_data).execute()
            data = response.data[0]
            if not data:
                raise Exception("Failed to add position")
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            raise e

        basic_position = Position(
            id=data["id"],
            portfolio_id=data["portfolio_id"],
            ticker=data["ticker"],
            total_shares=data["total_shares"],
            avg_buy_price=data["avg_buy_price"],
            updated_at=data["updated_at"],
        )

        try:
            enriched_position = self._get_enriched_position(basic_position)
        except Exception as e:
            logger.error(f"Error getting enriched position: {e}")
            raise e

        return PositionOut(
            **basic_position.model_dump(),
            current_price=enriched_position.current_price,
            current_market_value=enriched_position.current_market_value,
            unrealized_pnl=enriched_position.unrealized_pnl,
            unrealized_pnl_pct=enriched_position.unrealized_pnl_pct,
        )

    async def get_by_id(self, id: int) -> Optional[PositionOut]:
        response = self.db_client.table(self.table_name).select("*").eq("id", id).execute()
        data = response.data[0]
        if not data:
            raise Exception("Failed to get position")
        return PositionOut(**data)

    async def update(self, id: int, position: PositionPatch) -> Optional[PositionOut]:
        try:
            # mode='json'을 사용하여 Decimal을 자동으로 JSON 호환 타입으로 변환
            position_data = position.model_dump(mode="json", exclude_unset=True)
            response = self.db_client.table(self.table_name).update(position_data).eq("id", id).execute()
            data = response.data[0]
            if not data:
                raise Exception("Failed to update position")
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            raise e
        return PositionOut(**data)

    async def delete_by_id(self, id: int) -> bool:
        try:
            response = self.db_client.table(self.table_name).delete().eq("id", id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting position: {e}")
            raise e
