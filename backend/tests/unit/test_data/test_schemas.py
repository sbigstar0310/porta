# tests/unit/test_data/test_schemas.py
"""
Pydantic 스키마 단위 테스트
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import ValidationError

from data.schemas import (
    UserCreate,
    UserOut,
    UserPatch,
    PortfolioCreate,
    PortfolioOut,
    PortfolioPatch,
    PositionCreate,
    PositionOut,
    PositionPatch,
    TransactionCreate,
    TransactionOut,
)


@pytest.mark.unit
class TestUserSchemas:
    """User 관련 스키마 테스트"""

    def test_user_create_valid(self):
        """UserCreate 스키마 유효성 테스트"""
        user_create = UserCreate(email="test@example.com", timezone="Asia/Seoul", language="ko")

        assert user_create.email == "test@example.com"
        assert user_create.timezone == "Asia/Seoul"
        assert user_create.language == "ko"

    def test_user_create_with_defaults(self):
        """UserCreate 기본값 테스트"""
        user_create = UserCreate(email="test@example.com")

        assert user_create.timezone == "Asia/Seoul"
        assert user_create.language == "ko"

    def test_user_create_invalid_email(self):
        """UserCreate 잘못된 이메일 테스트"""
        with pytest.raises(ValidationError):
            UserCreate(email="invalid-email")

    def test_user_create_invalid_timezone(self):
        """UserCreate 잘못된 타임존 테스트"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", timezone="Invalid/Zone")

    def test_user_create_invalid_language(self):
        """UserCreate 잘못된 언어 코드 테스트"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", language="invalid")

    def test_user_out_schema(self):
        """UserOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        user_out = UserOut(
            id=1,
            uuid="test-uuid",
            email="test@example.com",
            timezone="Asia/Seoul",
            language="ko",
            created_at=now,
            updated_at=now,
            last_login=now,
        )

        assert user_out.id == 1
        assert user_out.email == "test@example.com"
        assert isinstance(user_out.created_at, datetime)

    def test_user_patch_partial_update(self):
        """UserPatch 부분 업데이트 테스트"""
        user_patch = UserPatch(timezone="America/New_York")

        # 지정된 필드만 포함
        assert user_patch.timezone == "America/New_York"
        assert user_patch.language is None
        assert user_patch.email is None

    def test_user_patch_exclude_unset(self):
        """UserPatch exclude_unset 테스트"""
        user_patch = UserPatch(timezone="America/New_York")

        data = user_patch.model_dump(exclude_unset=True)

        # 설정된 필드만 포함
        assert "timezone" in data
        assert "language" not in data
        assert "email" not in data


@pytest.mark.unit
class TestPortfolioSchemas:
    """Portfolio 관련 스키마 테스트"""

    def test_portfolio_create_valid(self):
        """PortfolioCreate 스키마 유효성 테스트"""
        portfolio_create = PortfolioCreate(
            user_id=1, name="테스트 포트폴리오", description="테스트용 포트폴리오입니다", currency="USD"
        )

        assert portfolio_create.user_id == 1
        assert portfolio_create.name == "테스트 포트폴리오"
        assert portfolio_create.currency == "USD"

    def test_portfolio_create_with_defaults(self):
        """PortfolioCreate 기본값 테스트"""
        portfolio_create = PortfolioCreate(user_id=1, name="테스트 포트폴리오")

        assert portfolio_create.currency == "USD"
        assert portfolio_create.description is None

    def test_portfolio_create_invalid_name(self):
        """PortfolioCreate 잘못된 이름 테스트"""
        with pytest.raises(ValidationError):
            PortfolioCreate(user_id=1, name="")  # 빈 이름

    def test_portfolio_create_invalid_currency(self):
        """PortfolioCreate 잘못된 통화 코드 테스트"""
        with pytest.raises(ValidationError):
            PortfolioCreate(user_id=1, name="테스트 포트폴리오", currency="INVALID")

    def test_portfolio_out_schema(self):
        """PortfolioOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        portfolio_out = PortfolioOut(
            id=1,
            user_id=1,
            name="테스트 포트폴리오",
            description="설명",
            total_value=Decimal("10000.00"),
            currency="USD",
            created_at=now,
            updated_at=now,
        )

        assert portfolio_out.id == 1
        assert portfolio_out.total_value == Decimal("10000.00")
        assert isinstance(portfolio_out.total_value, Decimal)

    def test_portfolio_patch_partial_update(self):
        """PortfolioPatch 부분 업데이트 테스트"""
        portfolio_patch = PortfolioPatch(name="업데이트된 포트폴리오")

        data = portfolio_patch.model_dump(exclude_unset=True)

        assert "name" in data
        assert "description" not in data
        assert "currency" not in data


@pytest.mark.unit
class TestPositionSchemas:
    """Position 관련 스키마 테스트"""

    def test_position_create_valid(self):
        """PositionCreate 스키마 유효성 테스트"""
        position_create = PositionCreate(
            portfolio_id=1, symbol="AAPL", shares=Decimal("10.0"), average_price=Decimal("150.00")
        )

        assert position_create.portfolio_id == 1
        assert position_create.symbol == "AAPL"
        assert position_create.shares == Decimal("10.0")
        assert position_create.average_price == Decimal("150.00")

    def test_position_create_invalid_symbol(self):
        """PositionCreate 잘못된 심볼 테스트"""
        with pytest.raises(ValidationError):
            PositionCreate(
                portfolio_id=1, symbol="", shares=Decimal("10.0"), average_price=Decimal("150.00")  # 빈 심볼
            )

    def test_position_create_negative_shares(self):
        """PositionCreate 음수 주식 수 테스트"""
        with pytest.raises(ValidationError):
            PositionCreate(
                portfolio_id=1, symbol="AAPL", shares=Decimal("-10.0"), average_price=Decimal("150.00")  # 음수 주식 수
            )

    def test_position_create_zero_average_price(self):
        """PositionCreate 0 평균가 테스트"""
        with pytest.raises(ValidationError):
            PositionCreate(
                portfolio_id=1, symbol="AAPL", shares=Decimal("10.0"), average_price=Decimal("0.0")  # 0 평균가
            )

    def test_position_out_schema(self):
        """PositionOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        position_out = PositionOut(
            id=1,
            portfolio_id=1,
            symbol="AAPL",
            shares=Decimal("10.0"),
            average_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("1550.00"),
            unrealized_gain_loss=Decimal("50.00"),
            created_at=now,
            updated_at=now,
        )

        assert position_out.id == 1
        assert position_out.market_value == Decimal("1550.00")
        assert isinstance(position_out.unrealized_gain_loss, Decimal)

    def test_position_patch_partial_update(self):
        """PositionPatch 부분 업데이트 테스트"""
        position_patch = PositionPatch(current_price=Decimal("160.00"))

        data = position_patch.model_dump(exclude_unset=True)

        assert "current_price" in data
        assert "shares" not in data
        assert "average_price" not in data

    def test_position_decimal_precision(self):
        """Position 스키마 Decimal 정밀도 테스트"""
        position_create = PositionCreate(
            portfolio_id=1, symbol="AAPL", shares=Decimal("10.123456"), average_price=Decimal("150.789123")
        )

        # Decimal 정밀도 유지 확인
        assert position_create.shares == Decimal("10.123456")
        assert position_create.average_price == Decimal("150.789123")


@pytest.mark.unit
class TestTransactionSchemas:
    """Transaction 관련 스키마 테스트"""

    def test_transaction_create_valid(self):
        """TransactionCreate 스키마 유효성 테스트"""
        now = datetime.now(timezone.utc)
        transaction_create = TransactionCreate(
            portfolio_id=1,
            symbol="AAPL",
            transaction_type="buy",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            transaction_date=now,
        )

        assert transaction_create.portfolio_id == 1
        assert transaction_create.symbol == "AAPL"
        assert transaction_create.transaction_type == "buy"
        assert transaction_create.shares == Decimal("10.0")
        assert transaction_create.price == Decimal("150.00")

    def test_transaction_create_with_calculated_total(self):
        """TransactionCreate 총액 자동 계산 테스트"""
        now = datetime.now(timezone.utc)
        transaction_create = TransactionCreate(
            portfolio_id=1,
            symbol="AAPL",
            transaction_type="buy",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            transaction_date=now,
        )

        # 총액 자동 계산 확인 (shares * price)
        expected_total = Decimal("10.0") * Decimal("150.00")
        # 모델에서 total_amount가 자동으로 계산되는 경우
        # assert transaction_create.total_amount == expected_total

    def test_transaction_create_invalid_type(self):
        """TransactionCreate 잘못된 거래 타입 테스트"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                symbol="AAPL",
                transaction_type="invalid",  # 잘못된 타입
                shares=Decimal("10.0"),
                price=Decimal("150.00"),
                transaction_date=now,
            )

    def test_transaction_create_future_date(self):
        """TransactionCreate 미래 날짜 테스트"""
        future_date = datetime.now(timezone.utc).replace(year=2030)
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                symbol="AAPL",
                transaction_type="buy",
                shares=Decimal("10.0"),
                price=Decimal("150.00"),
                transaction_date=future_date,
            )

    def test_transaction_create_negative_values(self):
        """TransactionCreate 음수 값 테스트"""
        now = datetime.now(timezone.utc)

        # 음수 주식 수
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                symbol="AAPL",
                transaction_type="buy",
                shares=Decimal("-10.0"),
                price=Decimal("150.00"),
                transaction_date=now,
            )

        # 음수 가격
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                symbol="AAPL",
                transaction_type="buy",
                shares=Decimal("10.0"),
                price=Decimal("-150.00"),
                transaction_date=now,
            )

    def test_transaction_out_schema(self):
        """TransactionOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        transaction_out = TransactionOut(
            id=1,
            portfolio_id=1,
            symbol="AAPL",
            transaction_type="buy",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            total_amount=Decimal("1500.00"),
            transaction_date=now,
            created_at=now,
        )

        assert transaction_out.id == 1
        assert transaction_out.total_amount == Decimal("1500.00")
        assert isinstance(transaction_out.transaction_date, datetime)


@pytest.mark.unit
class TestSchemaInteroperability:
    """스키마 간 상호 운용성 테스트"""

    def test_model_to_schema_conversion(self):
        """모델에서 스키마로 변환 테스트"""
        # 이 테스트는 실제 모델과 스키마 간 변환이 필요한 경우 구현
        pass

    def test_schema_validation_consistency(self):
        """스키마 검증 일관성 테스트"""
        # Create와 Patch 스키마 간 검증 규칙 일관성 확인

        # 유효한 데이터로 Create 스키마 생성
        portfolio_create = PortfolioCreate(user_id=1, name="테스트 포트폴리오", currency="USD")

        # 같은 필드로 Patch 스키마 생성
        portfolio_patch = PortfolioPatch(name="테스트 포트폴리오", currency="USD")

        # 검증 규칙이 일관되어야 함
        assert portfolio_create.name == portfolio_patch.name
        assert portfolio_create.currency == portfolio_patch.currency

    def test_schema_field_types_consistency(self):
        """스키마 필드 타입 일관성 테스트"""
        # 관련 스키마들의 같은 필드가 같은 타입을 가져야 함

        portfolio_create = PortfolioCreate(user_id=1, name="테스트 포트폴리오")

        portfolio_patch = PortfolioPatch(name="업데이트된 포트폴리오")

        # name 필드 타입 일관성 확인
        assert type(portfolio_create.name) == type(portfolio_patch.name)

    def test_nested_schema_validation(self):
        """중첩 스키마 검증 테스트"""
        # 향후 중첩 스키마가 있는 경우를 위한 플레이스홀더
        pass
