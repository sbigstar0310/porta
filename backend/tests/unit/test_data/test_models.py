# tests/unit/test_data/test_models.py
"""
Pydantic 모델 단위 테스트
"""
import pytest
from datetime import datetime, timezone, date
from decimal import Decimal
from pydantic import ValidationError

from data.models import User, Portfolio, Position, Transaction, Report, Schedule
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestUserModel:
    """User 모델 테스트"""

    def test_user_model_valid_data(self):
        """유효한 사용자 데이터로 모델 생성 테스트"""
        user_data = MockDataGenerator.create_user()
        user = User(**user_data)

        assert user.id == user_data["id"]
        assert user.uuid == user_data["uuid"]
        assert user.email == user_data["email"]
        assert user.timezone == user_data["timezone"]
        assert user.language == user_data["language"]
        assert user.email_verified == user_data["email_verified"]

    def test_user_model_default_values(self):
        """User 모델 기본값 테스트"""
        now = datetime.now(timezone.utc)
        user_data = {"id": 1, "created_at": now, "updated_at": now, "last_login": now}

        user = User(**user_data)

        # 기본값 확인
        assert user.timezone == "Asia/Seoul"
        assert user.language == "ko"
        assert user.uuid is None
        assert user.email is None
        assert user.email_verified is False

    def test_user_timezone_validation_valid(self):
        """유효한 타임존 검증 테스트"""
        valid_timezones = ["Asia/Seoul", "America/New_York", "Europe/London", "UTC"]

        for timezone_val in valid_timezones:
            user_data = MockDataGenerator.create_user(timezone=timezone_val)
            user = User(**user_data)
            assert user.timezone == timezone_val

    def test_user_timezone_validation_invalid(self):
        """유효하지 않은 타임존 검증 테스트 (허용되지 않는 문자)"""
        invalid_timezones = ["Asia Seoul", "Seoul!", ""]

        for timezone_val in invalid_timezones:
            user_data = MockDataGenerator.create_user(timezone=timezone_val)
            with pytest.raises(ValidationError):
                User(**user_data)

    def test_user_language_validation_valid(self):
        """유효한 언어 코드 검증 테스트"""
        valid_languages = ["ko", "en", "ja", "zh", "fr", "de"]

        for language in valid_languages:
            user_data = MockDataGenerator.create_user(language=language)
            user = User(**user_data)
            assert user.language == language

    def test_user_language_validation_invalid(self):
        """유효하지 않은 언어 코드 검증 테스트"""
        invalid_languages = ["kor", "eng", "korean", "english", "12"]

        for language in invalid_languages:
            user_data = MockDataGenerator.create_user(language=language)
            with pytest.raises(ValidationError):
                User(**user_data)

    def test_user_email_assignment(self):
        """이메일 필드 할당 테스트 (별도 형식 검증 없음)"""
        valid_emails = ["test@example.com", "user.name@domain.co.kr", "123@test.org"]

        for email in valid_emails:
            user_data = MockDataGenerator.create_user(email=email)
            user = User(**user_data)
            assert user.email == email


@pytest.mark.unit
class TestPortfolioModel:
    """Portfolio 모델 테스트"""

    def test_portfolio_model_valid_data(self):
        """유효한 포트폴리오 데이터로 모델 생성 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio()
        portfolio = Portfolio(**portfolio_data)

        assert portfolio.id == portfolio_data["id"]
        assert portfolio.user_id == portfolio_data["user_id"]
        assert portfolio.base_currency == portfolio_data["base_currency"]
        assert portfolio.cash == portfolio_data["cash"]

    def test_portfolio_cash_quantized(self):
        """포트폴리오 현금 소수점 둘째 자리 반올림 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio(cash=Decimal("12345.6789"))
        portfolio = Portfolio(**portfolio_data)

        # Decimal 타입 유지 및 소수점 둘째 자리 반올림 확인
        assert isinstance(portfolio.cash, Decimal)
        assert portfolio.cash == Decimal("12345.68")

    def test_portfolio_currency_validation(self):
        """통화 코드 검증 테스트"""
        valid_currencies = ["USD", "KRW", "EUR", "JPY", "GBP"]

        for currency in valid_currencies:
            portfolio_data = MockDataGenerator.create_portfolio(base_currency=currency)
            portfolio = Portfolio(**portfolio_data)
            assert portfolio.base_currency == currency

    def test_portfolio_currency_validation_invalid(self):
        """유효하지 않은 통화 코드 검증 테스트"""
        invalid_currencies = ["usd", "US", "DOLLAR", ""]

        for currency in invalid_currencies:
            portfolio_data = MockDataGenerator.create_portfolio(base_currency=currency)
            with pytest.raises(ValidationError):
                Portfolio(**portfolio_data)

    def test_portfolio_negative_cash_validation(self):
        """음수 현금 검증 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio(cash=Decimal("-100.00"))

        with pytest.raises(ValidationError):
            Portfolio(**portfolio_data)


@pytest.mark.unit
class TestPositionModel:
    """Position 모델 테스트"""

    def test_position_model_valid_data(self):
        """유효한 포지션 데이터로 모델 생성 테스트"""
        position_data = MockDataGenerator.create_position()
        position = Position(**position_data)

        assert position.id == position_data["id"]
        assert position.portfolio_id == position_data["portfolio_id"]
        assert position.ticker == position_data["ticker"]
        assert position.total_shares == position_data["total_shares"]
        assert position.avg_buy_price == position_data["avg_buy_price"]

    def test_position_decimal_quantized(self):
        """포지션 Decimal 소수점 둘째 자리 반올림 테스트"""
        position_data = MockDataGenerator.create_position(
            total_shares=Decimal("10.567"), avg_buy_price=Decimal("150.256")
        )
        position = Position(**position_data)

        # Decimal 타입 유지 및 반올림 확인
        assert isinstance(position.total_shares, Decimal)
        assert isinstance(position.avg_buy_price, Decimal)
        assert position.total_shares == Decimal("10.57")
        assert position.avg_buy_price == Decimal("150.26")

    def test_position_ticker_validation(self):
        """주식 티커 검증 테스트"""
        valid_tickers = ["AAPL", "MSFT", "GOOGL", "BRK-B", "BRK.B"]

        for ticker in valid_tickers:
            position_data = MockDataGenerator.create_position(ticker=ticker)
            position = Position(**position_data)
            assert position.ticker == ticker

    def test_position_ticker_normalized(self):
        """주식 티커 대문자 변환 테스트"""
        position_data = MockDataGenerator.create_position(ticker=" aapl ")
        position = Position(**position_data)

        assert position.ticker == "AAPL"

    def test_position_negative_shares_validation(self):
        """음수 주식 수 검증 테스트"""
        position_data = MockDataGenerator.create_position(total_shares=Decimal("-10.0"))

        # 음수 주식 수는 허용되지 않음 (공매도 제외)
        with pytest.raises(ValidationError):
            Position(**position_data)

    def test_position_zero_avg_buy_price_validation(self):
        """0 평균 매수가 검증 테스트"""
        position_data = MockDataGenerator.create_position(avg_buy_price=Decimal("0.0"))

        with pytest.raises(ValidationError):
            Position(**position_data)

    def test_position_zero_shares_allowed(self):
        """0 주식 수 허용 테스트 (전량 매도 후 상태)"""
        position_data = MockDataGenerator.create_position(total_shares=Decimal("0.0"))
        position = Position(**position_data)

        assert position.total_shares == Decimal("0.00")


@pytest.mark.unit
class TestTransactionModel:
    """Transaction 모델 테스트"""

    def test_transaction_model_valid_data(self):
        """유효한 거래 데이터로 모델 생성 테스트"""
        transaction_data = MockDataGenerator.create_transaction()
        transaction = Transaction(**transaction_data)

        assert transaction.id == transaction_data["id"]
        assert transaction.portfolio_id == transaction_data["portfolio_id"]
        assert transaction.ticker == transaction_data["ticker"]
        assert transaction.transaction_type == transaction_data["transaction_type"]

    def test_transaction_type_validation(self):
        """거래 타입 검증 테스트"""
        valid_types = ["BUY", "SELL"]

        for transaction_type in valid_types:
            transaction_data = MockDataGenerator.create_transaction(transaction_type=transaction_type)
            transaction = Transaction(**transaction_data)
            assert transaction.transaction_type == transaction_type

    def test_transaction_type_invalid(self):
        """유효하지 않은 거래 타입 테스트"""
        invalid_types = ["buy", "sell", "purchase", "trade", "HOLD"]

        for transaction_type in invalid_types:
            transaction_data = MockDataGenerator.create_transaction(transaction_type=transaction_type)
            with pytest.raises(ValidationError):
                Transaction(**transaction_data)

    def test_transaction_decimal_quantized(self):
        """거래 Decimal 소수점 둘째 자리 반올림 테스트"""
        transaction_data = MockDataGenerator.create_transaction(
            shares=Decimal("123.456789"), price=Decimal("987.654321"), fee=Decimal("1.005")
        )
        transaction = Transaction(**transaction_data)

        # Decimal 타입 유지 및 반올림 확인
        assert isinstance(transaction.shares, Decimal)
        assert isinstance(transaction.price, Decimal)
        assert isinstance(transaction.fee, Decimal)
        assert transaction.shares == Decimal("123.46")
        assert transaction.price == Decimal("987.65")
        assert transaction.fee == Decimal("1.01")

    def test_transaction_negative_values_validation(self):
        """음수 값 검증 테스트"""
        # 음수 주식 수
        transaction_data = MockDataGenerator.create_transaction(shares=Decimal("-10.0"))
        with pytest.raises(ValidationError):
            Transaction(**transaction_data)

        # 음수 가격
        transaction_data = MockDataGenerator.create_transaction(price=Decimal("-150.0"))
        with pytest.raises(ValidationError):
            Transaction(**transaction_data)

        # 음수 수수료
        transaction_data = MockDataGenerator.create_transaction(fee=Decimal("-1.0"))
        with pytest.raises(ValidationError):
            Transaction(**transaction_data)

    def test_transaction_date_type(self):
        """거래 날짜 타입 테스트 (date 타입)"""
        past_date = date(2020, 1, 15)
        transaction_data = MockDataGenerator.create_transaction(transaction_date=past_date)
        transaction = Transaction(**transaction_data)

        assert isinstance(transaction.transaction_date, date)
        assert transaction.transaction_date == past_date

    def test_transaction_currency_validation_invalid(self):
        """유효하지 않은 통화 코드 검증 테스트"""
        transaction_data = MockDataGenerator.create_transaction(currency="usd")

        with pytest.raises(ValidationError):
            Transaction(**transaction_data)


@pytest.mark.unit
class TestReportModel:
    """Report 모델 테스트"""

    def test_report_model_valid_data(self):
        """유효한 보고서 데이터로 모델 생성 테스트"""
        report_data = MockDataGenerator.create_report()
        report = Report(**report_data)

        assert report.id == report_data["id"]
        assert report.user_id == report_data["user_id"]
        assert report.report_md == report_data["report_md"]
        assert report.language == report_data["language"]

    def test_report_model_default_language(self):
        """Report 모델 기본 언어 테스트"""
        report_data = MockDataGenerator.create_report()
        del report_data["language"]

        report = Report(**report_data)
        assert report.language == "ko"


@pytest.mark.unit
class TestScheduleModel:
    """Schedule 모델 테스트"""

    def test_schedule_model_valid_data(self):
        """유효한 스케줄 데이터로 모델 생성 테스트"""
        schedule_data = MockDataGenerator.create_schedule()
        schedule = Schedule(**schedule_data)

        assert schedule.id == schedule_data["id"]
        assert schedule.user_id == schedule_data["user_id"]
        assert schedule.hour == schedule_data["hour"]
        assert schedule.minute == schedule_data["minute"]
        assert schedule.enabled == schedule_data["enabled"]

    def test_schedule_hour_range_validation(self):
        """스케줄 시간 범위 검증 테스트"""
        with pytest.raises(ValidationError):
            Schedule(**MockDataGenerator.create_schedule(hour=24))

        with pytest.raises(ValidationError):
            Schedule(**MockDataGenerator.create_schedule(hour=-1))

    def test_schedule_minute_range_validation(self):
        """스케줄 분 범위 검증 테스트"""
        with pytest.raises(ValidationError):
            Schedule(**MockDataGenerator.create_schedule(minute=60))

    def test_schedule_timezone_validation_invalid(self):
        """스케줄 잘못된 타임존 검증 테스트"""
        with pytest.raises(ValidationError):
            Schedule(**MockDataGenerator.create_schedule(timezone="Asia Seoul!"))


@pytest.mark.unit
class TestModelRelationships:
    """모델 간 관계 테스트"""

    def test_user_portfolio_relationship(self):
        """사용자-포트폴리오 관계 테스트"""
        user_data = MockDataGenerator.create_user(user_id=1)
        portfolio_data = MockDataGenerator.create_portfolio(user_id=1)

        user = User(**user_data)
        portfolio = Portfolio(**portfolio_data)

        # 외래키 관계 확인
        assert portfolio.user_id == user.id

    def test_portfolio_position_relationship(self):
        """포트폴리오-포지션 관계 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio(portfolio_id=1)
        position_data = MockDataGenerator.create_position(portfolio_id=1)

        portfolio = Portfolio(**portfolio_data)
        position = Position(**position_data)

        # 외래키 관계 확인
        assert position.portfolio_id == portfolio.id

    def test_portfolio_transaction_relationship(self):
        """포트폴리오-거래 관계 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio(portfolio_id=1)
        transaction_data = MockDataGenerator.create_transaction(portfolio_id=1)

        portfolio = Portfolio(**portfolio_data)
        transaction = Transaction(**transaction_data)

        # 외래키 관계 확인
        assert transaction.portfolio_id == portfolio.id

    def test_position_transaction_ticker_consistency(self):
        """포지션-거래 티커 일관성 테스트"""
        ticker = "AAPL"
        position_data = MockDataGenerator.create_position(ticker=ticker)
        transaction_data = MockDataGenerator.create_transaction(ticker=ticker)

        position = Position(**position_data)
        transaction = Transaction(**transaction_data)

        # 같은 티커인지 확인
        assert position.ticker == transaction.ticker == ticker


@pytest.mark.unit
class TestModelSerialization:
    """모델 직렬화/역직렬화 테스트"""

    def test_user_model_json_serialization(self):
        """User 모델 직렬화/역직렬화 테스트"""
        user_data = MockDataGenerator.create_user()
        user = User(**user_data)

        # 직렬화
        json_data = user.model_dump()

        # 역직렬화
        restored_user = User(**json_data)

        assert user.id == restored_user.id
        assert user.email == restored_user.email
        assert user.timezone == restored_user.timezone

    def test_portfolio_model_json_serialization(self):
        """Portfolio 모델 직렬화/역직렬화 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio()
        portfolio = Portfolio(**portfolio_data)

        # 직렬화 (model_dump는 Decimal 타입 유지)
        json_data = portfolio.model_dump()
        assert isinstance(json_data["cash"], Decimal)

        # 역직렬화
        restored_portfolio = Portfolio(**json_data)
        assert portfolio.cash == restored_portfolio.cash

    def test_model_validation_errors(self):
        """모델 검증 오류 테스트"""
        # 필수 필드 누락
        with pytest.raises(ValidationError) as exc_info:
            User(id=1)  # created_at, updated_at, last_login 누락

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["type"] == "missing" for error in errors)

    def test_model_extra_fields_ignored(self):
        """추가 필드 무시 테스트"""
        user_data = MockDataGenerator.create_user()
        user_data["extra_field"] = "should_be_ignored"

        # 추가 필드가 있어도 모델 생성 성공
        user = User(**user_data)

        # 추가 필드는 모델에 포함되지 않음
        assert not hasattr(user, "extra_field")
