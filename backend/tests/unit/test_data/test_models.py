# tests/unit/test_data/test_models.py
"""
Pydantic 모델 단위 테스트
"""
import pytest
from datetime import datetime, timezone, date
from decimal import Decimal
from pydantic import ValidationError

from data.models import User, Portfolio, Position, Transaction
from tests.fixtures.mock_data import MockDataGenerator


@pytest.mark.unit
class TestUserModel:
    """User 모델 테스트"""

    def test_user_model_valid_data(self):
        """유효한 사용자 데이터로 모델 생성 테스트"""
        user_data = MockDataGenerator.create_user()
        user = User(**user_data)

        assert user.id == user_data["id"]
        assert user.email == user_data["email"]
        assert user.timezone == user_data["timezone"]
        assert user.language == user_data["language"]

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

    def test_user_timezone_validation_valid(self):
        """유효한 타임존 검증 테스트"""
        valid_timezones = ["Asia/Seoul", "America/New_York", "Europe/London", "UTC"]

        for timezone_val in valid_timezones:
            user_data = MockDataGenerator.create_user(timezone=timezone_val)
            user = User(**user_data)
            assert user.timezone == timezone_val

    def test_user_timezone_validation_invalid(self):
        """유효하지 않은 타임존 검증 테스트"""
        invalid_timezones = ["Invalid/Zone", "ABC", "123/456"]

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
        invalid_languages = ["kor", "eng", "korean", "english", "123"]

        for language in invalid_languages:
            user_data = MockDataGenerator.create_user(language=language)
            with pytest.raises(ValidationError):
                User(**user_data)

    def test_user_email_validation(self):
        """이메일 형식 검증 테스트 (Pydantic의 기본 이메일 검증 사용)"""
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
        assert portfolio.name == portfolio_data["name"]
        assert portfolio.currency == portfolio_data["currency"]

    def test_portfolio_decimal_precision(self):
        """포트폴리오 총 가치 Decimal 정밀도 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio(total_value=Decimal("12345.6789"))
        portfolio = Portfolio(**portfolio_data)

        # Decimal 타입 유지 확인
        assert isinstance(portfolio.total_value, Decimal)
        assert portfolio.total_value == Decimal("12345.6789")

    def test_portfolio_currency_validation(self):
        """통화 코드 검증 테스트"""
        valid_currencies = ["USD", "KRW", "EUR", "JPY", "GBP"]

        for currency in valid_currencies:
            portfolio_data = MockDataGenerator.create_portfolio(currency=currency)
            portfolio = Portfolio(**portfolio_data)
            assert portfolio.currency == currency

    def test_portfolio_name_validation(self):
        """포트폴리오 이름 검증 테스트"""
        # 빈 이름은 허용되지 않음
        portfolio_data = MockDataGenerator.create_portfolio(name="")
        with pytest.raises(ValidationError):
            Portfolio(**portfolio_data)

        # 유효한 이름들
        valid_names = ["포트폴리오 1", "My Portfolio", "테스트_포트폴리오", "Portfolio-2024"]
        for name in valid_names:
            portfolio_data = MockDataGenerator.create_portfolio(name=name)
            portfolio = Portfolio(**portfolio_data)
            assert portfolio.name == name


@pytest.mark.unit
class TestPositionModel:
    """Position 모델 테스트"""

    def test_position_model_valid_data(self):
        """유효한 포지션 데이터로 모델 생성 테스트"""
        position_data = MockDataGenerator.create_position()
        position = Position(**position_data)

        assert position.id == position_data["id"]
        assert position.portfolio_id == position_data["portfolio_id"]
        assert position.symbol == position_data["symbol"]
        assert position.shares == position_data["shares"]

    def test_position_decimal_calculations(self):
        """포지션 Decimal 계산 테스트"""
        position_data = MockDataGenerator.create_position(
            shares=Decimal("10.5"), average_price=Decimal("150.25"), current_price=Decimal("160.75")
        )
        position = Position(**position_data)

        # Decimal 타입 유지 확인
        assert isinstance(position.shares, Decimal)
        assert isinstance(position.average_price, Decimal)
        assert isinstance(position.current_price, Decimal)
        assert isinstance(position.market_value, Decimal)
        assert isinstance(position.unrealized_gain_loss, Decimal)

    def test_position_symbol_validation(self):
        """주식 심볼 검증 테스트"""
        valid_symbols = ["AAPL", "MSFT", "GOOGL", "BRK-B", "BRK.B"]

        for symbol in valid_symbols:
            position_data = MockDataGenerator.create_position(symbol=symbol)
            position = Position(**position_data)
            assert position.symbol == symbol

    def test_position_negative_shares_validation(self):
        """음수 주식 수 검증 테스트"""
        position_data = MockDataGenerator.create_position(shares=Decimal("-10.0"))

        # 음수 주식 수는 허용되지 않음 (공매도 제외)
        with pytest.raises(ValidationError):
            Position(**position_data)

    def test_position_zero_price_validation(self):
        """0 가격 검증 테스트"""
        # 평균 매수가가 0인 경우
        position_data = MockDataGenerator.create_position(average_price=Decimal("0.0"))
        with pytest.raises(ValidationError):
            Position(**position_data)

        # 현재가가 0인 경우 (상장폐지 등의 경우 허용될 수 있음)
        position_data = MockDataGenerator.create_position(current_price=Decimal("0.0"))
        position = Position(**position_data)
        assert position.current_price == Decimal("0.0")


@pytest.mark.unit
class TestTransactionModel:
    """Transaction 모델 테스트"""

    def test_transaction_model_valid_data(self):
        """유효한 거래 데이터로 모델 생성 테스트"""
        transaction_data = MockDataGenerator.create_transaction()
        transaction = Transaction(**transaction_data)

        assert transaction.id == transaction_data["id"]
        assert transaction.portfolio_id == transaction_data["portfolio_id"]
        assert transaction.symbol == transaction_data["symbol"]
        assert transaction.transaction_type == transaction_data["transaction_type"]

    def test_transaction_type_validation(self):
        """거래 타입 검증 테스트"""
        valid_types = ["buy", "sell"]

        for transaction_type in valid_types:
            transaction_data = MockDataGenerator.create_transaction(transaction_type=transaction_type)
            transaction = Transaction(**transaction_data)
            assert transaction.transaction_type == transaction_type

    def test_transaction_type_invalid(self):
        """유효하지 않은 거래 타입 테스트"""
        invalid_types = ["purchase", "sale", "trade", "hold"]

        for transaction_type in invalid_types:
            transaction_data = MockDataGenerator.create_transaction(transaction_type=transaction_type)
            with pytest.raises(ValidationError):
                Transaction(**transaction_data)

    def test_transaction_decimal_precision(self):
        """거래 Decimal 정밀도 테스트"""
        transaction_data = MockDataGenerator.create_transaction(
            shares=Decimal("123.456789"), price=Decimal("987.654321"), total_amount=Decimal("121932.100907")
        )
        transaction = Transaction(**transaction_data)

        # Decimal 타입과 정밀도 유지 확인
        assert isinstance(transaction.shares, Decimal)
        assert isinstance(transaction.price, Decimal)
        assert isinstance(transaction.total_amount, Decimal)
        assert transaction.shares == Decimal("123.456789")

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

    def test_transaction_date_validation(self):
        """거래 날짜 검증 테스트"""
        # 미래 날짜는 허용되지 않음
        future_date = datetime.now(timezone.utc).replace(year=2030)
        transaction_data = MockDataGenerator.create_transaction(transaction_date=future_date)

        with pytest.raises(ValidationError):
            Transaction(**transaction_data)

        # 과거 날짜는 허용됨
        past_date = datetime.now(timezone.utc).replace(year=2020)
        transaction_data = MockDataGenerator.create_transaction(transaction_date=past_date)
        transaction = Transaction(**transaction_data)
        assert transaction.transaction_date == past_date


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

    def test_position_transaction_symbol_consistency(self):
        """포지션-거래 심볼 일관성 테스트"""
        symbol = "AAPL"
        position_data = MockDataGenerator.create_position(symbol=symbol)
        transaction_data = MockDataGenerator.create_transaction(symbol=symbol)

        position = Position(**position_data)
        transaction = Transaction(**transaction_data)

        # 같은 심볼인지 확인
        assert position.symbol == transaction.symbol == symbol


@pytest.mark.unit
class TestModelSerialization:
    """모델 직렬화/역직렬화 테스트"""

    def test_user_model_json_serialization(self):
        """User 모델 JSON 직렬화 테스트"""
        user_data = MockDataGenerator.create_user()
        user = User(**user_data)

        # JSON 직렬화
        json_data = user.model_dump()

        # 역직렬화
        restored_user = User(**json_data)

        assert user.id == restored_user.id
        assert user.email == restored_user.email
        assert user.timezone == restored_user.timezone

    def test_portfolio_model_json_serialization(self):
        """Portfolio 모델 JSON 직렬화 테스트"""
        portfolio_data = MockDataGenerator.create_portfolio()
        portfolio = Portfolio(**portfolio_data)

        # JSON 직렬화
        json_data = portfolio.model_dump()

        # Decimal은 문자열로 직렬화됨
        assert isinstance(json_data["total_value"], Decimal)

        # 역직렬화
        restored_portfolio = Portfolio(**json_data)
        assert portfolio.total_value == restored_portfolio.total_value

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
