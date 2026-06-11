# tests/unit/test_repo/test_recommendation_repo.py
"""
RecommendationRepo 단위 테스트

현재 구현 기준:
- 모든 공개 메서드는 async
- create()는 create_many() 위임, create_many()는 빈 리스트 입력 시 즉시 [] 반환
- get_recent()는 user_id + created_at(gte since) 필터 + 최신순 정렬
- update()는 exclude_none 패치, 빈 패치면 get_by_id()로 폴백
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

from repo.recommendation_repo import RecommendationRepo
from data.schemas import RecommendationCreate, RecommendationOut, RecommendationReturnsPatch
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestRecommendationRepo:
    """RecommendationRepo 테스트 클래스"""

    @pytest.fixture
    def mock_db_client(self):
        """Mock Supabase 클라이언트"""
        return MagicMock()

    @pytest.fixture
    def recommendation_repo(self, mock_db_client):
        """RecommendationRepo 인스턴스 (Mock 클라이언트 직접 주입)"""
        return RecommendationRepo(db_client=mock_db_client)

    @pytest.fixture
    def sample_recommendation_row(self):
        """테스트용 recommendations 테이블 행"""
        return MockDataGenerator.create_recommendation(recommendation_id=1, user_id=1, ticker="AAPL")

    @pytest.fixture
    def sample_recommendation_create(self):
        """테스트용 추천 생성 스키마"""
        return RecommendationCreate(
            user_id=1,
            report_id=1,
            ticker="AAPL",
            action="BUY",
            total_score=75.0,
            momo_score=70.0,
            fund_score=80.0,
            target_weight_pct=10.0,
            price_at_rec=150.0,
            confidence=80.0,
            reason="모멘텀/펀더멘털 모두 양호",
        )

    # ===== 초기화 =====

    def test_recommendation_repo_initialization(self, mock_db_client):
        """RecommendationRepo 초기화: 기본 테이블 이름은 recommendations"""
        repo = RecommendationRepo(db_client=mock_db_client)

        assert repo.db_client is mock_db_client
        assert repo.table_name == "recommendations"

    # ===== create_many =====

    async def test_create_many_empty_list_returns_empty(self, recommendation_repo, mock_db_client):
        """빈 리스트 입력 시 DB 호출 없이 [] 반환"""
        result = await recommendation_repo.create_many([])

        assert result == []
        mock_db_client.table.assert_not_called()

    async def test_create_many_bulk_insert(
        self, recommendation_repo, mock_db_client, sample_recommendation_create
    ):
        """여러 추천 일괄 insert: rows 직렬화 및 RecommendationOut 리스트 반환"""
        schemas = [
            sample_recommendation_create,
            RecommendationCreate(user_id=1, ticker="MSFT", action="HOLD", price_at_rec=320.0),
        ]
        rows = [
            MockDataGenerator.create_recommendation(recommendation_id=1, user_id=1, ticker="AAPL"),
            MockDataGenerator.create_recommendation(recommendation_id=2, user_id=1, ticker="MSFT", action="HOLD"),
        ]
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = rows

        result = await recommendation_repo.create_many(schemas)

        # insert는 mode='json' 직렬화된 행 목록으로 1회 호출
        mock_db_client.table.assert_called_with("recommendations")
        mock_db_client.table.return_value.insert.assert_called_once_with(
            [schema.model_dump(mode="json") for schema in schemas]
        )

        assert len(result) == 2
        assert all(isinstance(r, RecommendationOut) for r in result)
        assert result[0].ticker == "AAPL"
        assert result[1].ticker == "MSFT"

    async def test_create_many_empty_response_raises(
        self, recommendation_repo, mock_db_client, sample_recommendation_create
    ):
        """insert 응답이 비어 있으면 ValueError 발생"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = []

        with pytest.raises(ValueError):
            await recommendation_repo.create_many([sample_recommendation_create])

    async def test_create_delegates_to_create_many(
        self, recommendation_repo, mock_db_client, sample_recommendation_create, sample_recommendation_row
    ):
        """create(): create_many에 위임하고 첫 번째 결과 반환"""
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [sample_recommendation_row]

        result = await recommendation_repo.create(sample_recommendation_create)

        assert isinstance(result, RecommendationOut)
        assert result.id == sample_recommendation_row["id"]
        assert result.ticker == "AAPL"

    # ===== get_by_id =====

    async def test_get_by_id_success(self, recommendation_repo, mock_db_client, sample_recommendation_row):
        """ID로 추천 조회 성공"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = [sample_recommendation_row]

        result = await recommendation_repo.get_by_id(1)

        select_chain.eq.assert_called_with("id", 1)
        assert isinstance(result, RecommendationOut)
        assert result.id == 1

    async def test_get_by_id_not_found(self, recommendation_repo, mock_db_client):
        """조회 결과 없으면 None 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = []

        result = await recommendation_repo.get_by_id(999)

        assert result is None

    # ===== get_recent =====

    async def test_get_recent_filters_by_user_and_since(self, recommendation_repo, mock_db_client):
        """최근 추천 조회: user_id eq + created_at gte(since) + 최신순 정렬"""
        rows = [
            MockDataGenerator.create_recommendation(recommendation_id=i + 1, user_id=1, ticker="AAPL")
            for i in range(3)
        ]
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = rows

        result = await recommendation_repo.get_recent(user_id=1, days=30)

        # 체인 호출 검증
        select_chain.eq.assert_called_with("user_id", 1)
        gte_args = select_chain.eq.return_value.gte.call_args[0]
        assert gte_args[0] == "created_at"
        # since는 약 30일 전 UTC ISO 문자열이어야 함
        since = datetime.fromisoformat(gte_args[1])
        expected = datetime.now(timezone.utc) - timedelta(days=30)
        assert abs((since - expected).total_seconds()) < 60
        select_chain.eq.return_value.gte.return_value.order.assert_called_with("created_at", desc=True)

        # 결과 검증
        assert len(result) == 3
        assert all(isinstance(r, RecommendationOut) for r in result)
        assert all(r.user_id == 1 for r in result)

    async def test_get_recent_empty_data_returns_empty_list(self, recommendation_repo, mock_db_client):
        """응답 data가 None이어도 빈 리스트 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = None

        result = await recommendation_repo.get_recent(user_id=1)

        assert result == []

    # ===== update =====

    async def test_update_excludes_none_fields(self, recommendation_repo, mock_db_client, sample_recommendation_row):
        """채점 결과 갱신: None 필드는 패치에서 제외"""
        patch_schema = RecommendationReturnsPatch(return_7d=5.2, benchmark_return_7d=1.1)
        updated_row = {**sample_recommendation_row, "return_7d": 5.2, "benchmark_return_7d": 1.1}
        update_chain = mock_db_client.table.return_value.update
        update_chain.return_value.eq.return_value.execute.return_value.data = [updated_row]

        result = await recommendation_repo.update(1, patch_schema)

        update_chain.assert_called_with({"return_7d": 5.2, "benchmark_return_7d": 1.1})
        update_chain.return_value.eq.assert_called_with("id", 1)
        assert isinstance(result, RecommendationOut)
        assert result.return_7d == 5.2
        assert result.benchmark_return_7d == 1.1

    async def test_update_empty_patch_falls_back_to_get_by_id(
        self, recommendation_repo, mock_db_client, sample_recommendation_row
    ):
        """빈 패치(모든 필드 None)면 update 호출 없이 get_by_id 결과 반환"""
        select_chain = mock_db_client.table.return_value.select.return_value
        select_chain.eq.return_value.execute.return_value.data = [sample_recommendation_row]

        result = await recommendation_repo.update(1, RecommendationReturnsPatch())

        mock_db_client.table.return_value.update.assert_not_called()
        select_chain.eq.assert_called_with("id", 1)
        assert isinstance(result, RecommendationOut)
        assert result.id == sample_recommendation_row["id"]

    async def test_update_not_found_returns_none(self, recommendation_repo, mock_db_client):
        """업데이트 대상이 없으면 None 반환"""
        mock_db_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        result = await recommendation_repo.update(999, RecommendationReturnsPatch(return_7d=1.0))

        assert result is None

    # ===== delete_by_id =====

    async def test_delete_by_id_success(self, recommendation_repo, mock_db_client):
        """추천 삭제 성공: True 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = [{"id": 1}]

        result = await recommendation_repo.delete_by_id(1)

        delete_chain.eq.assert_called_with("id", 1)
        assert result is True

    async def test_delete_by_id_not_found(self, recommendation_repo, mock_db_client):
        """삭제 대상이 없으면 False 반환"""
        delete_chain = mock_db_client.table.return_value.delete.return_value
        delete_chain.eq.return_value.execute.return_value.data = []

        result = await recommendation_repo.delete_by_id(999)

        assert result is False

    async def test_delete_by_id_db_error_propagates(self, recommendation_repo, mock_db_client):
        """삭제 중 DB 예외 발생 시 그대로 전파"""
        mock_db_client.table.return_value.delete.return_value.eq.return_value.execute.side_effect = Exception(
            "DB Error"
        )

        with pytest.raises(Exception, match="DB Error"):
            await recommendation_repo.delete_by_id(1)
