# tests/unit/test_repo/test_base_repo.py
"""
BaseRepo 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from abc import ABC
from supabase import Client
from pydantic import BaseModel

from repo.base_repo import BaseRepo


class TestSchema(BaseModel):
    """테스트용 스키마"""

    id: int
    name: str


class ConcreteRepo(BaseRepo):
    """테스트용 구체적인 Repository 구현"""

    async def create(self, schema: TestSchema, **kwargs):
        response = self.db_client.table(self.table_name).insert(schema.dict()).execute()
        return response.data[0] if response.data else None

    async def get_by_id(self, id: int, **kwargs):
        response = self.db_client.table(self.table_name).select("*").eq("id", id).execute()
        return response.data[0] if response.data else None

    async def update(self, schema: TestSchema, **kwargs):
        response = self.db_client.table(self.table_name).update(schema.dict()).eq("id", schema.id).execute()
        return response.data[0] if response.data else None

    async def delete_by_id(self, id: int):
        response = self.db_client.table(self.table_name).delete().eq("id", id).execute()
        return response.data[0] if response.data else None


@pytest.mark.unit
class TestBaseRepo:
    """BaseRepo 테스트 클래스"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase 클라이언트"""
        mock_client = MagicMock(spec=Client)

        # Mock table operations
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        # Mock insert
        mock_insert = MagicMock()
        mock_insert.execute.return_value.data = [{"id": 1, "name": "test"}]
        mock_table.insert.return_value = mock_insert

        # Mock select
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value.data = [{"id": 1, "name": "test"}]
        mock_table.select.return_value = mock_select

        # Mock update
        mock_update = MagicMock()
        mock_update.eq.return_value = mock_update
        mock_update.execute.return_value.data = [{"id": 1, "name": "updated"}]
        mock_table.update.return_value = mock_update

        # Mock delete
        mock_delete = MagicMock()
        mock_delete.eq.return_value = mock_delete
        mock_delete.execute.return_value.data = [{"id": 1}]
        mock_table.delete.return_value = mock_delete

        return mock_client

    @pytest.fixture
    def concrete_repo(self, mock_supabase_client):
        """구체적인 Repository 인스턴스"""
        return ConcreteRepo(mock_supabase_client, "test_table")

    def test_base_repo_initialization(self, mock_supabase_client):
        """BaseRepo 초기화 테스트"""
        table_name = "test_table"
        repo = ConcreteRepo(mock_supabase_client, table_name)

        assert repo.db_client == mock_supabase_client
        assert repo.table_name == table_name

    def test_base_repo_is_abstract(self):
        """BaseRepo가 추상 클래스인지 확인"""
        assert issubclass(BaseRepo, ABC)

        # 추상 메서드들이 정의되어 있는지 확인
        abstract_methods = BaseRepo.__abstractmethods__
        expected_methods = {"create", "get_by_id", "update", "delete_by_id"}
        assert abstract_methods == expected_methods

    async def test_create_operation(self, concrete_repo, mock_supabase_client):
        """Create 연산 테스트"""
        test_schema = TestSchema(id=1, name="test")

        result = await concrete_repo.create(test_schema)

        # Supabase 호출 검증
        mock_supabase_client.table.assert_called_with("test_table")
        mock_supabase_client.table("test_table").insert.assert_called_with(test_schema.dict())

        # 결과 검증
        assert result == {"id": 1, "name": "test"}

    async def test_get_by_id_operation(self, concrete_repo, mock_supabase_client):
        """Get by ID 연산 테스트"""
        test_id = 1

        result = await concrete_repo.get_by_id(test_id)

        # Supabase 호출 검증
        mock_supabase_client.table.assert_called_with("test_table")
        mock_supabase_client.table("test_table").select.assert_called_with("*")
        mock_supabase_client.table("test_table").select("*").eq.assert_called_with("id", test_id)

        # 결과 검증
        assert result == {"id": 1, "name": "test"}

    async def test_update_operation(self, concrete_repo, mock_supabase_client):
        """Update 연산 테스트"""
        test_schema = TestSchema(id=1, name="updated")

        result = await concrete_repo.update(test_schema)

        # Supabase 호출 검증
        mock_supabase_client.table.assert_called_with("test_table")
        mock_supabase_client.table("test_table").update.assert_called_with(test_schema.dict())
        mock_supabase_client.table("test_table").update(test_schema.dict()).eq.assert_called_with("id", test_schema.id)

        # 결과 검증
        assert result == {"id": 1, "name": "updated"}

    async def test_delete_by_id_operation(self, concrete_repo, mock_supabase_client):
        """Delete by ID 연산 테스트"""
        test_id = 1

        result = await concrete_repo.delete_by_id(test_id)

        # Supabase 호출 검증
        mock_supabase_client.table.assert_called_with("test_table")
        mock_supabase_client.table("test_table").delete.assert_called_with()
        mock_supabase_client.table("test_table").delete().eq.assert_called_with("id", test_id)

        # 결과 검증
        assert result == {"id": 1}

    async def test_create_operation_empty_response(self, concrete_repo, mock_supabase_client):
        """Create 연산 빈 응답 테스트"""
        # 빈 응답 설정
        mock_supabase_client.table("test_table").insert().execute.return_value.data = []

        test_schema = TestSchema(id=1, name="test")
        result = await concrete_repo.create(test_schema)

        assert result is None

    async def test_get_by_id_not_found(self, concrete_repo, mock_supabase_client):
        """Get by ID 결과 없음 테스트"""
        # 빈 응답 설정
        mock_supabase_client.table("test_table").select("*").eq().execute.return_value.data = []

        result = await concrete_repo.get_by_id(999)

        assert result is None

    def test_table_name_property(self, concrete_repo):
        """테이블 이름 속성 테스트"""
        assert concrete_repo.table_name == "test_table"

    def test_db_client_property(self, concrete_repo, mock_supabase_client):
        """DB 클라이언트 속성 테스트"""
        assert concrete_repo.db_client == mock_supabase_client
