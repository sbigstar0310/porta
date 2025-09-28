from abc import ABC, abstractmethod
from supabase import Client
from typing import Any
from pydantic import BaseModel


class BaseRepo(ABC):
    """Base Repository Class (CRUD)"""

    def __init__(self, db_client: Client, table_name: str):
        self.db_client = db_client
        self.table_name = table_name

    @abstractmethod
    async def create(self, schema: BaseModel, **kwargs) -> dict | Any | None:
        pass

    @abstractmethod
    async def get_by_id(self, id: int, **kwargs) -> dict | Any | None:
        pass

    @abstractmethod
    async def update(self, schema: BaseModel, **kwargs) -> dict | Any | None:
        pass

    @abstractmethod
    async def delete_by_id(self, id: int) -> dict | Any | None:
        pass
