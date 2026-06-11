# tests/unit/test_data/test_schemas.py
"""
Pydantic 스키마 단위 테스트
"""
import pytest
from datetime import datetime, timezone, date
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
    ReportCreate,
    ReportOut,
    RecommendationCreate,
    ScheduleCreate,
    SchedulePatch,
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
        assert user_create.password is None

    def test_user_create_short_password(self):
        """UserCreate 8자 미만 비밀번호 테스트"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="short")

    def test_user_create_valid_password(self):
        """UserCreate 유효한 비밀번호 테스트"""
        user_create = UserCreate(email="test@example.com", password="password123")
        assert user_create.password == "password123"

    def test_user_create_invalid_timezone(self):
        """UserCreate 잘못된 타임존 테스트 (허용되지 않는 문자 포함)"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", timezone="Asia Seoul!")

    def test_user_create_invalid_language(self):
        """UserCreate 잘못된 언어 코드 테스트"""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", language="invalid")

    def test_user_create_language_lowercased(self):
        """UserCreate 언어 코드 소문자 변환 테스트"""
        user_create = UserCreate(email="test@example.com", language="KO")
        assert user_create.language == "ko"

    def test_user_out_schema(self):
        """UserOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        user_out = UserOut(
            id=1,
            email="test@example.com",
            timezone="Asia/Seoul",
            language="ko",
            created_at=now,
            updated_at=now,
            last_login=now,
        )

        assert user_out.id == 1
        assert user_out.email == "test@example.com"
        assert user_out.email_verified is False  # 기본값
        assert user_out.access_token is None  # 로그인 시에만 포함
        assert isinstance(user_out.created_at, datetime)

    def test_user_out_with_tokens(self):
        """UserOut 토큰 포함 테스트 (로그인 응답)"""
        now = datetime.now(timezone.utc)
        user_out = UserOut(
            id=1,
            email="test@example.com",
            timezone="Asia/Seoul",
            language="ko",
            email_verified=True,
            created_at=now,
            updated_at=now,
            last_login=now,
            access_token="access-token",
            refresh_token="refresh-token",
            token_type="Bearer",
            expires_in=3600,
        )

        assert user_out.email_verified is True
        assert user_out.access_token == "access-token"
        assert user_out.token_type == "Bearer"
        assert user_out.expires_in == 3600

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

    def test_user_patch_invalid_language(self):
        """UserPatch 잘못된 언어 코드 테스트"""
        with pytest.raises(ValidationError):
            UserPatch(language="kor")


@pytest.mark.unit
class TestPortfolioSchemas:
    """Portfolio 관련 스키마 테스트"""

    def test_portfolio_create_valid(self):
        """PortfolioCreate 스키마 유효성 테스트"""
        portfolio_create = PortfolioCreate(user_id=1, base_currency="USD", cash=Decimal("1000.00"))

        assert portfolio_create.user_id == 1
        assert portfolio_create.base_currency == "USD"
        assert portfolio_create.cash == Decimal("1000.00")

    def test_portfolio_create_with_defaults(self):
        """PortfolioCreate 기본값 테스트"""
        portfolio_create = PortfolioCreate(user_id=1)

        assert portfolio_create.base_currency == "USD"
        assert portfolio_create.cash == Decimal("0.00")

    def test_portfolio_create_invalid_currency(self):
        """PortfolioCreate 잘못된 통화 코드 테스트"""
        with pytest.raises(ValidationError):
            PortfolioCreate(user_id=1, base_currency="INVALID")

    def test_portfolio_create_negative_cash(self):
        """PortfolioCreate 음수 현금 테스트"""
        with pytest.raises(ValidationError):
            PortfolioCreate(user_id=1, cash=Decimal("-100.00"))

    def test_portfolio_create_cash_quantized(self):
        """PortfolioCreate 현금 소수점 둘째 자리 반올림 테스트"""
        portfolio_create = PortfolioCreate(user_id=1, cash=Decimal("1234.5678"))

        assert portfolio_create.cash == Decimal("1234.57")

    def test_portfolio_out_schema(self):
        """PortfolioOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        portfolio_out = PortfolioOut(
            id=1,
            user_id=1,
            base_currency="USD",
            cash=Decimal("10000.00"),
            updated_at=now,
        )

        assert portfolio_out.id == 1
        assert portfolio_out.cash == Decimal("10000.00")
        assert portfolio_out.positions == []  # 기본값은 빈 목록
        assert portfolio_out.total_value is None  # 실시간 계산 필드는 옵셔널

    def test_portfolio_out_with_positions(self):
        """PortfolioOut 포지션 포함 테스트"""
        now = datetime.now(timezone.utc)
        position = PositionOut(
            id=1,
            portfolio_id=1,
            ticker="AAPL",
            total_shares=Decimal("10.5"),
            avg_buy_price=Decimal("150.25"),
            updated_at=now,
        )
        portfolio_out = PortfolioOut(
            id=1,
            user_id=1,
            base_currency="USD",
            cash=Decimal("1200.00"),
            updated_at=now,
            positions=[position],
            total_stock_value=Decimal("1737.75"),
            total_value=Decimal("2937.75"),
        )

        assert len(portfolio_out.positions) == 1
        assert portfolio_out.positions[0].ticker == "AAPL"
        assert portfolio_out.total_value == Decimal("2937.75")

    def test_portfolio_patch_partial_update(self):
        """PortfolioPatch 부분 업데이트 테스트"""
        portfolio_patch = PortfolioPatch(cash=Decimal("5000.00"))

        data = portfolio_patch.model_dump(exclude_unset=True)

        assert "cash" in data
        assert "base_currency" not in data

    def test_portfolio_patch_invalid_currency(self):
        """PortfolioPatch 잘못된 통화 코드 테스트"""
        with pytest.raises(ValidationError):
            PortfolioPatch(base_currency="usd")  # 소문자는 허용되지 않음


@pytest.mark.unit
class TestPositionSchemas:
    """Position 관련 스키마 테스트"""

    def test_position_create_valid(self):
        """PositionCreate 스키마 유효성 테스트"""
        position_create = PositionCreate(
            portfolio_id=1, ticker="AAPL", total_shares=Decimal("10.0"), avg_buy_price=Decimal("150.00")
        )

        assert position_create.portfolio_id == 1
        assert position_create.ticker == "AAPL"
        assert position_create.total_shares == Decimal("10.0")
        assert position_create.avg_buy_price == Decimal("150.00")

    def test_position_create_missing_fields(self):
        """PositionCreate 필수 필드 누락 테스트"""
        with pytest.raises(ValidationError):
            PositionCreate(portfolio_id=1, ticker="AAPL")  # total_shares, avg_buy_price 누락

    def test_position_out_schema(self):
        """PositionOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        position_out = PositionOut(
            id=1,
            portfolio_id=1,
            ticker="AAPL",
            total_shares=Decimal("10.0"),
            avg_buy_price=Decimal("150.00"),
            updated_at=now,
            current_price=Decimal("155.00"),
            current_market_value=Decimal("1550.00"),
            unrealized_pnl=Decimal("50.00"),
            unrealized_pnl_pct=Decimal("3.33"),
        )

        assert position_out.id == 1
        assert position_out.current_market_value == Decimal("1550.00")
        assert isinstance(position_out.unrealized_pnl, Decimal)

    def test_position_out_optional_calculated_fields(self):
        """PositionOut 계산 필드 옵셔널 테스트"""
        now = datetime.now(timezone.utc)
        position_out = PositionOut(
            id=1,
            portfolio_id=1,
            ticker="AAPL",
            total_shares=Decimal("10.0"),
            avg_buy_price=Decimal("150.00"),
            updated_at=now,
        )

        assert position_out.current_price is None
        assert position_out.current_market_value is None
        assert position_out.unrealized_pnl is None

    def test_position_patch_partial_update(self):
        """PositionPatch 부분 업데이트 테스트"""
        position_patch = PositionPatch(total_shares=Decimal("20.0"))

        data = position_patch.model_dump(exclude_unset=True)

        assert "total_shares" in data
        assert "ticker" not in data
        assert "avg_buy_price" not in data

    def test_position_patch_negative_shares(self):
        """PositionPatch 음수 주식 수 테스트"""
        with pytest.raises(ValidationError):
            PositionPatch(total_shares=Decimal("-10.0"))

    def test_position_patch_zero_avg_buy_price(self):
        """PositionPatch 0 평균 매수가 테스트"""
        with pytest.raises(ValidationError):
            PositionPatch(avg_buy_price=Decimal("0.0"))

    def test_position_create_decimal_precision(self):
        """PositionCreate Decimal 정밀도 테스트 (별도 반올림 없음)"""
        position_create = PositionCreate(
            portfolio_id=1, ticker="AAPL", total_shares=Decimal("10.123456"), avg_buy_price=Decimal("150.789123")
        )

        # Create 스키마는 정밀도를 그대로 유지함
        assert position_create.total_shares == Decimal("10.123456")
        assert position_create.avg_buy_price == Decimal("150.789123")


@pytest.mark.unit
class TestTransactionSchemas:
    """Transaction 관련 스키마 테스트"""

    def test_transaction_create_valid(self):
        """TransactionCreate 스키마 유효성 테스트"""
        transaction_create = TransactionCreate(
            portfolio_id=1,
            ticker="AAPL",
            transaction_type="BUY",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            transaction_date=date.today(),
        )

        assert transaction_create.portfolio_id == 1
        assert transaction_create.ticker == "AAPL"
        assert transaction_create.transaction_type == "BUY"
        assert transaction_create.shares == Decimal("10.00")
        assert transaction_create.price == Decimal("150.00")

    def test_transaction_create_defaults(self):
        """TransactionCreate 기본값 테스트"""
        transaction_create = TransactionCreate(
            portfolio_id=1,
            ticker="AAPL",
            transaction_type="SELL",
            shares=Decimal("5.0"),
            price=Decimal("160.00"),
            transaction_date=date.today(),
        )

        assert transaction_create.fee == Decimal("0.00")
        assert transaction_create.currency == "USD"
        assert transaction_create.exchange == ""
        assert transaction_create.notes is None

    def test_transaction_create_ticker_normalized(self):
        """TransactionCreate 티커 대문자 변환 테스트"""
        transaction_create = TransactionCreate(
            portfolio_id=1,
            ticker=" aapl ",
            transaction_type="BUY",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            transaction_date=date.today(),
        )

        assert transaction_create.ticker == "AAPL"

    def test_transaction_create_invalid_type(self):
        """TransactionCreate 잘못된 거래 타입 테스트"""
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                ticker="AAPL",
                transaction_type="buy",  # 소문자는 허용되지 않음 (BUY/SELL)
                shares=Decimal("10.0"),
                price=Decimal("150.00"),
                transaction_date=date.today(),
            )

    def test_transaction_create_invalid_currency(self):
        """TransactionCreate 잘못된 통화 코드 테스트"""
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                ticker="AAPL",
                transaction_type="BUY",
                shares=Decimal("10.0"),
                price=Decimal("150.00"),
                transaction_date=date.today(),
                currency="INVALID",
            )

    def test_transaction_create_negative_values(self):
        """TransactionCreate 음수 값 테스트"""
        # 음수 주식 수
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                ticker="AAPL",
                transaction_type="BUY",
                shares=Decimal("-10.0"),
                price=Decimal("150.00"),
                transaction_date=date.today(),
            )

        # 음수 가격
        with pytest.raises(ValidationError):
            TransactionCreate(
                portfolio_id=1,
                ticker="AAPL",
                transaction_type="BUY",
                shares=Decimal("10.0"),
                price=Decimal("-150.00"),
                transaction_date=date.today(),
            )

    def test_transaction_create_decimal_quantized(self):
        """TransactionCreate 소수점 둘째 자리 반올림 테스트"""
        transaction_create = TransactionCreate(
            portfolio_id=1,
            ticker="AAPL",
            transaction_type="BUY",
            shares=Decimal("10.123456"),
            price=Decimal("150.789123"),
            transaction_date=date.today(),
        )

        assert transaction_create.shares == Decimal("10.12")
        assert transaction_create.price == Decimal("150.79")

    def test_transaction_out_schema(self):
        """TransactionOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        transaction_out = TransactionOut(
            id=1,
            portfolio_id=1,
            ticker="AAPL",
            transaction_type="BUY",
            shares=Decimal("10.0"),
            price=Decimal("150.00"),
            transaction_date=date.today(),
            fee=Decimal("0.00"),
            currency="USD",
            exchange="NASDAQ",
            notes=None,
            created_at=now,
        )

        assert transaction_out.id == 1
        assert transaction_out.ticker == "AAPL"
        assert isinstance(transaction_out.transaction_date, date)


@pytest.mark.unit
class TestReportSchemas:
    """Report 관련 스키마 테스트"""

    def test_report_create_valid(self):
        """ReportCreate 스키마 유효성 테스트"""
        report_create = ReportCreate(user_id=1, report_md="# 보고서", language="ko")

        assert report_create.user_id == 1
        assert report_create.report_md == "# 보고서"
        assert report_create.language == "ko"

    def test_report_create_empty_content(self):
        """ReportCreate 빈 보고서 내용 테스트"""
        with pytest.raises(ValidationError):
            ReportCreate(user_id=1, report_md="")

    def test_report_create_invalid_language(self):
        """ReportCreate 잘못된 언어 코드 테스트"""
        with pytest.raises(ValidationError):
            ReportCreate(user_id=1, report_md="# 보고서", language="kor")

    def test_report_out_schema(self):
        """ReportOut 스키마 테스트"""
        now = datetime.now(timezone.utc)
        report_out = ReportOut(id=1, user_id=1, created_at=now, report_md="# 보고서", language="ko")

        assert report_out.id == 1
        assert report_out.report_md == "# 보고서"


@pytest.mark.unit
class TestRecommendationSchemas:
    """Recommendation 관련 스키마 테스트"""

    def test_recommendation_create_valid(self):
        """RecommendationCreate 스키마 유효성 테스트"""
        rec_create = RecommendationCreate(
            user_id=1,
            report_id=1,
            ticker="AAPL",
            action="BUY",
            price_at_rec=150.0,
            confidence=80.0,
        )

        assert rec_create.user_id == 1
        assert rec_create.ticker == "AAPL"
        assert rec_create.action == "BUY"
        assert rec_create.price_at_rec == 150.0

    def test_recommendation_create_invalid_action(self):
        """RecommendationCreate 잘못된 액션 테스트"""
        with pytest.raises(ValidationError):
            RecommendationCreate(user_id=1, ticker="AAPL", action="STRONG_BUY", price_at_rec=150.0)

    def test_recommendation_create_zero_price(self):
        """RecommendationCreate 0 가격 테스트"""
        with pytest.raises(ValidationError):
            RecommendationCreate(user_id=1, ticker="AAPL", action="BUY", price_at_rec=0.0)

    def test_recommendation_create_invalid_confidence(self):
        """RecommendationCreate 범위 밖 확신도 테스트"""
        with pytest.raises(ValidationError):
            RecommendationCreate(user_id=1, ticker="AAPL", action="BUY", price_at_rec=150.0, confidence=150.0)


@pytest.mark.unit
class TestScheduleSchemas:
    """Schedule 관련 스키마 테스트"""

    def test_schedule_create_valid(self):
        """ScheduleCreate 스키마 유효성 테스트"""
        schedule_create = ScheduleCreate(user_id=1, hour=9, minute=30)

        assert schedule_create.user_id == 1
        assert schedule_create.hour == 9
        assert schedule_create.minute == 30
        assert schedule_create.timezone == "Asia/Seoul"  # 기본값
        assert schedule_create.enabled is True  # 기본값

    def test_schedule_create_invalid_hour(self):
        """ScheduleCreate 범위 밖 시간 테스트"""
        with pytest.raises(ValidationError):
            ScheduleCreate(user_id=1, hour=24, minute=0)

    def test_schedule_create_invalid_minute(self):
        """ScheduleCreate 범위 밖 분 테스트"""
        with pytest.raises(ValidationError):
            ScheduleCreate(user_id=1, hour=9, minute=60)

    def test_schedule_patch_partial_update(self):
        """SchedulePatch 부분 업데이트 테스트"""
        schedule_patch = SchedulePatch(enabled=False)

        data = schedule_patch.model_dump(exclude_unset=True)

        assert "enabled" in data
        assert "hour" not in data
        assert "minute" not in data


@pytest.mark.unit
class TestSchemaInteroperability:
    """스키마 간 상호 운용성 테스트"""

    def test_schema_validation_consistency(self):
        """스키마 검증 일관성 테스트 (Create와 Patch 간 검증 규칙)"""
        # 유효한 데이터로 Create 스키마 생성
        portfolio_create = PortfolioCreate(user_id=1, base_currency="USD", cash=Decimal("1000.00"))

        # 같은 필드로 Patch 스키마 생성
        portfolio_patch = PortfolioPatch(base_currency="USD", cash=Decimal("1000.00"))

        # 검증 규칙이 일관되어야 함
        assert portfolio_create.base_currency == portfolio_patch.base_currency
        assert portfolio_create.cash == portfolio_patch.cash

    def test_schema_field_types_consistency(self):
        """스키마 필드 타입 일관성 테스트"""
        # 관련 스키마들의 같은 필드가 같은 타입을 가져야 함
        position_create = PositionCreate(
            portfolio_id=1, ticker="AAPL", total_shares=Decimal("10.0"), avg_buy_price=Decimal("150.00")
        )
        position_patch = PositionPatch(ticker="AAPL", total_shares=Decimal("10.0"))

        # ticker / total_shares 필드 타입 일관성 확인
        assert type(position_create.ticker) is type(position_patch.ticker)
        assert type(position_create.total_shares) is type(position_patch.total_shares)

    def test_nested_schema_validation(self):
        """중첩 스키마 검증 테스트 (PortfolioOut → PositionOut)"""
        now = datetime.now(timezone.utc)

        # dict 형태의 포지션도 PositionOut으로 검증되어야 함
        portfolio_out = PortfolioOut(
            id=1,
            user_id=1,
            base_currency="USD",
            cash=Decimal("1000.00"),
            updated_at=now,
            positions=[
                {
                    "id": 1,
                    "portfolio_id": 1,
                    "ticker": "AAPL",
                    "total_shares": Decimal("10.0"),
                    "avg_buy_price": Decimal("150.00"),
                    "updated_at": now,
                }
            ],
        )

        assert isinstance(portfolio_out.positions[0], PositionOut)
        assert portfolio_out.positions[0].ticker == "AAPL"
