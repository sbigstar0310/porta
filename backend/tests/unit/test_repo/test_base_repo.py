# tests/unit/test_repo/test_base_repo.py
"""
BaseRepo 단위 테스트

BaseRepo는 추상 클래스이므로 테스트용 구체 구현(ConcreteRepo)을 만들어
초기화/추상 메서드 정의/기본 CRUD 위임 동작을 검증한다.
"""
import pytest
from unittest.mock import MagicMock
from abc import ABC
from pydantic import BaseModel

from repo.base_repo import BaseRepo


class ItemSchema(BaseModel):
    """테스트용 스키마 (pytest 수집 대상이 되지 않도록 Test 접두사 회피)"""

    id: int
    name: str


class ConcreteRepo(BaseRepo):
    """테스트용 구체 Repository 구현"""

    async def create(self, schema: ItemSchema, **kwargs):
        response = self.db_client.table(self.table_name).insert(schema.model_dump()).execute()
        return response.data[0] if response.data else None

    async def get_by_id(self, id: int, **kwargs):
        response = self.db_client.table(self.table_name).select("*").eq("id", id).execute()
        return response.data[0] if response.data else None

    async def update(self, schema: ItemSchema, **kwargs):
        response = self.db_client.table(self.table_name).update(schema.model_dump()).eq("id", schema.id).execute()
        return response.data[0] if response.data else None

    async def delete_by_id(self, id: int):
        response = self.db_client.table(self.table_name).delete().eq("id", id).execute()
        return response.data[0] if response.data else None


@pytest.mark.unit
class TestBaseRepo:
    """BaseRepo 테스트 클래스"""

    @pytest.fixture
    def mock_db_client(self):
        """Mock Supabase 클라이언트 (spec 없이 — auth 등 동적 속성 접근 허용)"""
        mock_client = MagicMock()

        # insert 체인
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": 1, "name": "test"}]
        # select 체인
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": 1, "name": "test"}
        ]
        # update 체인
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"id": 1, "name": "updated"}
        ]
        # delete 체인
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [{"id": 1}]

        return mock_client

    @pytest.fixture
    def concrete_repo(self, mock_db_client):
        """구체 Repository 인스턴스"""
        return ConcreteRepo(mock_db_client, "test_table")

    def test_base_repo_initialization(self, mock_db_client):
        """BaseRepo 초기화 테스트: db_client/table_name 보관 확인"""
        repo = ConcreteRepo(mock_db_client, "test_table")

        assert repo.db_client is mock_db_client
        assert repo.table_name == "test_table"

    def test_base_repo_is_abstract(self):
        """BaseRepo가 추상 클래스이고 CRUD 추상 메서드를 정의하는지 확인"""
        assert issubclass(BaseRepo, ABC)
        assert BaseRepo.__abstractmethods__ == {"create", "get_by_id", "update", "delete_by_id"}

    def test_base_repo_cannot_be_instantiated(self, mock_db_client):
        """BaseRepo는 직접 인스턴스화할 수 없음"""
        with pytest.raises(TypeError):
            BaseRepo(mock_db_client, "test_table")

    async def test_create_operation(self, concrete_repo, mock_db_client):
        """Create 연산: insert 체인 호출 및 결과 반환 확인"""
        schema = ItemSchema(id=1, name="test")

        result = await concrete_repo.create(schema)

        mock_db_client.table.assert_called_with("test_table")
        mock_db_client.table.return_value.insert.assert_called_with(schema.model_dump())
        assert result == {"id": 1, "name": "test"}

    async def test_get_by_id_operation(self, concrete_repo, mock_db_client):
        """Get by ID 연산: select("*").eq("id", id) 체인 호출 확인"""
        result = await concrete_repo.get_by_id(1)

        mock_db_client.table.assert_called_with("test_table")
        mock_db_client.table.return_value.select.assert_called_with("*")
        mock_db_client.table.return_value.select.return_value.eq.assert_called_with("id", 1)
        assert result == {"id": 1, "name": "test"}

    async def test_update_operation(self, concrete_repo, mock_db_client):
        """Update 연산: update(...).eq("id", id) 체인 호출 확인"""
        schema = ItemSchema(id=1, name="updated")

        result = await concrete_repo.update(schema)

        mock_db_client.table.return_value.update.assert_called_with(schema.model_dump())
        mock_db_client.table.return_value.update.return_value.eq.assert_called_with("id", schema.id)
        assert result == {"id": 1, "name": "updated"}

    async def test_delete_by_id_operation(self, concrete_repo, mock_db_client):
        """Delete by ID 연산: delete().eq("id", id) 체인 호출 확인"""
        result = await concrete_repo.delete_by_id(1)

        mock_db_client.table.return_value.delete.assert_called_with()
        mock_db_client.table.return_value.delete.return_value.eq.assert_called_with("id", 1)
        assert result == {"id": 1}

    async def test_create_operation_empty_response(self, concrete_repo, mock_db_client):
        """Create 연산: 빈 응답이면 None 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = []

        result = await concrete_repo.create(ItemSchema(id=1, name="test"))

        assert result is None

    async def test_get_by_id_not_found(self, concrete_repo, mock_db_client):
        """Get by ID 연산: 결과 없으면 None 반환"""
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        result = await concrete_repo.get_by_id(999)

        assert result is None
