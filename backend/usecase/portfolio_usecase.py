from typing import Optional
from repo import PortfolioRepo
from data.schemas import PortfolioOut, PortfolioPatch, PortfolioCreate
import asyncio
import logging

logger = logging.getLogger(__name__)


class PortfolioUsecase:
    def __init__(self, portfolio_repo: PortfolioRepo):
        self.portfolio_repo = portfolio_repo

    async def get_current_portfolio(self, user_id: int) -> Optional[PortfolioOut]:
        result = await self.portfolio_repo.get_by_user_id(user_id)
        if not result:
            # Create portfolio manually if not found
            logger.warning(f"Portfolio not found for user {user_id}, creating new portfolio")
            result = await self.portfolio_repo.create(schema=PortfolioCreate(user_id=user_id))
        return result

    def get_current_portfolio_sync(self, user_id: int) -> Optional[PortfolioOut]:
        # 새로운 이벤트 루프 생성하여 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.portfolio_repo.get_by_user_id(user_id))
            if not result:
                # Create portfolio manually if not found
                logger.warning(f"Portfolio not found for user {user_id}, creating new portfolio")
                result = loop.run_until_complete(self.portfolio_repo.create(schema=PortfolioCreate(user_id=user_id)))
            return result
        finally:
            loop.close()

    async def update_portfolio(self, user_id: int, portfolio: PortfolioPatch) -> Optional[PortfolioOut]:
        return await self.portfolio_repo.update_by_user_id(user_id, portfolio)
