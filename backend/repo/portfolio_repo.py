import aiosqlite
from typing import List
from decimal import Decimal
from models import Portfolio, Position
from schemas import PortfolioOut, PositionOut
from clients.stock_client import StockClient


class PortfolioRepo:
    def __init__(self):
        self.stock_client = StockClient()

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
            async with aiosqlite.connect("porta.db") as db:
                cursor = await db.execute(
                    """
                    SELECT id, user_id, base_currency, cash, updated_at
                    FROM portfolios WHERE user_id = ?
                    """,
                    (user_id,),
                )
                row = await cursor.fetchone()

                if row:
                    from datetime import datetime

                    return Portfolio(
                        id=row[0],
                        user_id=row[1],
                        base_currency=row[2],
                        cash=Decimal(str(row[3])),
                        updated_at=datetime.fromisoformat(row[4].replace(" ", "T")),
                    )
                return None
        except Exception as e:
            print(f"Error fetching portfolio for user {user_id}: {e}")
            return None

    async def get_portfolio_positions(self, portfolio_id: int = 1) -> List[Position]:
        """DB에서 현재 포지션 조회

        Args:
            portfolio_id: 포트폴리오 ID (기본 1)

        Returns:
            List[Position]: List of Position
        """
        try:
            async with aiosqlite.connect("porta.db") as db:
                cursor = await db.execute(
                    """
                    SELECT id, portfolio_id, ticker, total_shares, avg_buy_price, updated_at
                    FROM positions
                    WHERE portfolio_id = ? AND total_shares > 0
                    ORDER BY ticker
                    """,
                    (portfolio_id,),
                )
                rows = await cursor.fetchall()

                positions = []
                for row in rows:
                    positions.append(
                        Position(
                            id=row[0],
                            portfolio_id=row[1],
                            ticker=row[2],
                            total_shares=Decimal(str(row[3])),
                            avg_buy_price=Decimal(str(row[4])),
                            updated_at=row[5],
                        )
                    )
                return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []

    async def get_current_portfolio(self, user_id: int = 1) -> PortfolioOut:
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
                raise ValueError(f"Portfolio not found for user {user_id}")

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
