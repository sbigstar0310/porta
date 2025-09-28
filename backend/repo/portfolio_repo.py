from typing import List, Optional
from decimal import Decimal
from data.models import Portfolio, Position
from data.schemas import PortfolioOut, PortfolioPatch, PositionOut, PortfolioCreate
from clients.stock_client import StockClient
from supabase import Client
from dateutil import parser as date_parser
from .base_repo import BaseRepo
import logging


logger = logging.getLogger(__name__)


class PortfolioRepo(BaseRepo):
    def __init__(self, stock_client: StockClient, db_client: Client, table_name: str = "portfolios"):
        super().__init__(db_client, table_name)
        self.stock_client = stock_client or StockClient()


    def _get_enriched_position(self, position: Position, current_price: Decimal) -> PositionOut:
        """포지션별 실시간 계산 필드들 계산 (현재가, 시장가치, 미실현 손익, 미실현 손익 비율)

        Args:
            position: 포지션 모델
            current_price: 현재 가격

        Returns:
            PositionOut: 포지션 출력 모델
        """
        total_shares = position.total_shares
        avg_buy_price = position.avg_buy_price

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

    async def get_portfolio_by_user(self, user_id: int = 1) -> Portfolio | None:
        """DB에서 사용자의 포트폴리오 정보 조회 (user_id 기준)

        Args:
            user_id: 사용자 ID (기본 1)

        Returns:
            Portfolio | None: 포트폴리오 모델
        """
        try:
            if not self.db_client:
                raise ValueError("DB client not initialized")

            response = self.db_client.table(self.table_name).select("*").eq("user_id", user_id).single().execute()
            if response.data:
                data = response.data
                return Portfolio(
                    id=data["id"],
                    user_id=data["user_id"],
                    base_currency=data["base_currency"],
                    cash=Decimal(str(data["cash"])),
                    updated_at=date_parser.parse(data["updated_at"]),

                )
            return None

        except Exception as e:
            logger.error(f"Error fetching portfolio for user {user_id}: {e}")
            return None

    async def get_portfolio_positions(self, portfolio_id: int = 1) -> List[Position]:
        """DB에서 현재 포지션 조회

        Args:
            portfolio_id: 포트폴리오 ID (기본 1)

        Returns:
            List[Position]: List of Position
        """
        try:

            if not self.db_client:
                raise ValueError("DB client not initialized")

            response = self.db_client.table("positions").select("*").eq("portfolio_id", portfolio_id).execute()
            if response.data:
                data = response.data
                return [
                    Position(
                        id=p["id"],
                        portfolio_id=p["portfolio_id"],
                        ticker=p["ticker"],
                        total_shares=Decimal(str(p["total_shares"])),
                        avg_buy_price=Decimal(str(p["avg_buy_price"])),
                        updated_at=date_parser.parse(p["updated_at"]),

                    )
                    for p in data
                ]
            return []

        except Exception as e:
            logger.error(f"Error fetching positions for portfolio {portfolio_id}: {e}")
            return []

    async def get_by_user_id(self, user_id: int = 1) -> Optional[PortfolioOut]:
        """
        현재 포트폴리오 완전한 정보 조회

        Args:
            user_id: 사용자 ID (기본 1)

        Returns:
            PortfolioOut: 포트폴리오 출력 모델
        """
        try:
            # get portfolio basic info
            portfolio_basic = await self.get_portfolio_by_user(user_id)
            if not portfolio_basic:
                logger.warning(f"Portfolio not found for user {user_id}")
                return None

            # get portfolio positions
            portfolio_id = portfolio_basic.id
            positions: List[Position] = await self.get_portfolio_positions(portfolio_id)
            if not positions:
                return PortfolioOut(
                    **portfolio_basic.model_dump(),
                    positions=[],
                    total_stock_value=Decimal("0.00"),
                    total_value=portfolio_basic.cash,
                )

            # get current prices
            tickers = [pos.ticker for pos in positions]
            current_prices = self.stock_client.get_stock_current_price(tickers)

            enriched_positions: List[PositionOut] = []
            total_market_value = Decimal("0.00")
            total_unrealized_pnl = Decimal("0.00")

            for pos in positions:
                ticker = pos.ticker
                current_price = current_prices.get(
                    ticker, pos.avg_buy_price
                )  # current_price가 없으면 avg_buy_price 사용 (이미 Decimal)
                # current_price가 Decimal이 아닌 경우 변환
                if not isinstance(current_price, Decimal):
                    current_price = Decimal(str(current_price))

                enriched_pos = self._get_enriched_position(pos, current_price)
                enriched_positions.append(enriched_pos)
                total_market_value += enriched_pos.current_market_value
                total_unrealized_pnl += enriched_pos.unrealized_pnl

            # 포트폴리오 레벨 계산
            total_cost_basis = sum(pos.total_shares * pos.avg_buy_price for pos in positions)
            total_unrealized_pnl_pct = (
                (total_unrealized_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else Decimal("0.00")
            )

            return PortfolioOut(
                **portfolio_basic.model_dump(),
                positions=enriched_positions,
                total_stock_value=total_market_value,
                total_value=portfolio_basic.cash + total_market_value,
                total_unrealized_pnl=total_unrealized_pnl,
                total_unrealized_pnl_pct=total_unrealized_pnl_pct,
            )

        except Exception as e:
            raise e

    async def get_by_id(self, portfolio_id: int) -> PortfolioOut:
        """
        포트폴리오 정보 조회
        """
        try:
            response = self.db_client.table(self.table_name).select("*").eq("id", portfolio_id).single().execute()
            if response.data:
                return PortfolioOut(**response.data)
            return None
        except Exception as e:
            raise e

    async def create(self, schema: PortfolioCreate) -> PortfolioOut:
        """
        포트폴리오 생성
        """
        try:
            response = self.db_client.table(self.table_name).insert(schema.model_dump(mode="json")).execute()
            if response.data and len(response.data) > 0:
                created_portfolio = PortfolioOut(**response.data[0])
                return created_portfolio
            else:
                logger.error(f"포트폴리오 생성 실패: 응답 데이터가 없습니다. response: {response}")
                raise ValueError("포트폴리오 생성 실패: 응답 데이터가 없습니다")
        except Exception as e:
            logger.error(f"포트폴리오 생성 중 예외 발생: {e}")
            raise e

    async def update_by_user_id(self, user_id: int, schema: PortfolioPatch) -> PortfolioOut:
        """
        포트폴리오 정보 업데이트

        Args:
            user_id: 사용자 ID
            schema: 포트폴리오 정보
        """
        try:
            if not self.db_client:
                raise ValueError("DB client not initialized")

            response = (
                self.db_client.table(self.table_name)
                .update(schema.model_dump(mode="json", exclude_none=True))
                .eq("user_id", user_id)
                .execute()
            )
            data = response.data[0]
            if data:
                logger.info(f"Updated portfolio: {data}")
                return PortfolioOut(**data)
            return None
        except Exception as e:
            raise e

    async def update(self, schema: PortfolioPatch) -> PortfolioOut:
        """
        포트폴리오 정보 업데이트
        """
        try:
            response = (
                self.db_client.table(self.table_name)
                .update(schema.model_dump(mode="json", exclude_none=True))
                .eq("id", schema.id)
                .single()
                .execute()
            )
            return PortfolioOut(**response.data)
        except Exception as e:
            raise e

    async def delete_by_id(self, portfolio_id: int) -> bool:
        """
        포트폴리오 정보 삭제
        """
        try:
            response = self.db_client.table(self.table_name).delete().eq("id", portfolio_id).execute()
            return len(response.data) > 0
        except Exception as e:
            raise e
