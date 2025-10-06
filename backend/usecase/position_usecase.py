from typing import Optional
from repo import PositionRepo
from data.schemas import PositionOut, PositionCreate, PositionPatch
import logging

logger = logging.getLogger(__name__)


class PositionUsecase:
    def __init__(self, position_repo: Optional[PositionRepo] = None):
        self.position_repo = position_repo

    async def create_position(self, position: PositionCreate) -> Optional[PositionOut]:
        return await self.position_repo.create(position)

    async def get_position(self, position_id: int) -> Optional[PositionOut]:
        return await self.position_repo.get_by_id(position_id)

    async def update_position(self, position_id: int, position: PositionPatch) -> Optional[PositionOut]:
        return await self.position_repo.update(position_id, position)

    async def delete_position(self, position_id: int) -> bool:
        return await self.position_repo.delete_by_id(position_id)
