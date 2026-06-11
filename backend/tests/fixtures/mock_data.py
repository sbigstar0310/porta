# tests/fixtures/mock_data.py
"""테스트용 Mock 데이터 생성기.

polyfactory 기반: 각 팩토리가 data/models.py·data/schemas.py의 Pydantic 모델에
바인딩되어 있어, 스키마에 필드가 추가되면 자동으로 따라온다 (생성기 수정 불필요).
명시적으로 고정하는 것은 ① 검증기 제약이 있는 필드(timezone/ticker/currency 등)와
② 테스트가 값을 단언하는 의미 있는 필드뿐이다. 필드 이름이 바뀌면 해당 고정값에서
즉시 에러가 나므로, 이 파일이 스키마 드리프트 감지기 역할도 한다.

기존 MockDataGenerator의 공개 API(create_* 메서드, 반환 dict)는 그대로 유지한다.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

from polyfactory.factories.pydantic_factory import ModelFactory

from data.models import Portfolio, Position, Report, Schedule, Transaction, User
from data.schemas import RecommendationOut


class _BaseFactory(ModelFactory):
    """공통 설정: 모델 기본값을 우선 사용하고, 나머지만 타입 기반 자동 생성."""

    __is_base_factory__ = True
    __use_defaults__ = True


class _UserFactory(_BaseFactory):
    __model__ = User
    timezone = "Asia/Seoul"  # 검증기 패턴 제약
    language = "ko"
    email_verified = False


class _PortfolioFactory(_BaseFactory):
    __model__ = Portfolio
    base_currency = "USD"  # 검증기 제약
    cash = Decimal("10000.00")


class _PositionFactory(_BaseFactory):
    __model__ = Position
    total_shares = Decimal("10.00")
    avg_buy_price = Decimal("150.00")


class _TransactionFactory(_BaseFactory):
    __model__ = Transaction
    transaction_type = "BUY"
    shares = Decimal("10.00")
    price = Decimal("150.00")
    fee = Decimal("0.00")
    currency = "USD"  # 검증기 제약
    exchange = "NASDAQ"
    notes = None


class _ReportFactory(_BaseFactory):
    __model__ = Report
    report_md = "# 포트폴리오 분석 보고서\n\n## 요약\n테스트용 보고서입니다."
    language = "ko"


class _ScheduleFactory(_BaseFactory):
    __model__ = Schedule
    hour = 9
    minute = 0
    timezone = "Asia/Seoul"  # 검증기 패턴 제약
    enabled = True


class _RecommendationFactory(_BaseFactory):
    __model__ = RecommendationOut
    action = "BUY"
    total_score = 75.0
    momo_score = 70.0
    fund_score = 80.0
    target_weight_pct = 10.0
    price_at_rec = 150.0
    confidence = 80.0
    reason = "테스트용 추천 사유"
    # 채점 전 상태가 기본 (return_* None)
    return_7d = None
    return_30d = None
    return_60d = None
    benchmark_return_7d = None
    benchmark_return_30d = None
    benchmark_return_60d = None


def _build(factory: type[ModelFactory], pins: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """유효한 베이스를 팩토리로 생성한 뒤, 오버라이드는 검증 없이 dict에 적용한다.

    오버라이드를 빌드에 넣지 않는 이유: "잘못된 값이 ValidationError를 내는가" 류의
    테스트가 invalid 값을 오버라이드로 주입하는데, 팩토리 빌드 시점에 검증되면
    테스트의 pytest.raises 바깥에서 터진다 (기존 생성기 의미론 유지).
    """
    data = factory.build(**pins).model_dump()
    data.update(overrides)
    return data


class MockDataGenerator:
    """테스트용 Mock 데이터 생성 클래스 (반환은 dict — 기존 API 유지)"""

    @staticmethod
    def create_user(user_id: int = 1, **overrides) -> Dict[str, Any]:
        """테스트용 사용자 데이터 생성 (users 테이블)"""
        pins = {"id": user_id, "uuid": f"test-uuid-{user_id}", "email": f"test{user_id}@example.com"}
        return _build(_UserFactory, pins, overrides)

    @staticmethod
    def create_portfolio(portfolio_id: int = 1, user_id: int = 1, **overrides) -> Dict[str, Any]:
        """테스트용 포트폴리오 데이터 생성 (portfolios 테이블)"""
        pins = {"id": portfolio_id, "user_id": user_id}
        return _build(_PortfolioFactory, pins, overrides)

    @staticmethod
    def create_position(
        position_id: int = 1, portfolio_id: int = 1, ticker: str = "AAPL", **overrides
    ) -> Dict[str, Any]:
        """테스트용 포지션 데이터 생성 (positions 테이블)"""
        pins = {"id": position_id, "portfolio_id": portfolio_id, "ticker": ticker}
        return _build(_PositionFactory, pins, overrides)

    @staticmethod
    def create_transaction(
        transaction_id: int = 1, portfolio_id: int = 1, ticker: str = "AAPL", **overrides
    ) -> Dict[str, Any]:
        """테스트용 거래 데이터 생성 (transactions 테이블)"""
        pins = {
            "id": transaction_id,
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "transaction_date": date.today(),
        }
        return _build(_TransactionFactory, pins, overrides)

    @staticmethod
    def create_report(report_id: int = 1, user_id: int = 1, **overrides) -> Dict[str, Any]:
        """테스트용 보고서 데이터 생성 (reports 테이블)"""
        pins = {"id": report_id, "user_id": user_id}
        return _build(_ReportFactory, pins, overrides)

    @staticmethod
    def create_schedule(schedule_id: int = 1, user_id: int = 1, **overrides) -> Dict[str, Any]:
        """테스트용 스케줄 데이터 생성 (schedules 테이블)"""
        pins = {"id": schedule_id, "user_id": user_id}
        return _build(_ScheduleFactory, pins, overrides)

    @staticmethod
    def create_recommendation(
        recommendation_id: int = 1, user_id: int = 1, ticker: str = "AAPL", **overrides
    ) -> Dict[str, Any]:
        """테스트용 추천 기록 데이터 생성 (recommendations 테이블)"""
        pins = {"id": recommendation_id, "user_id": user_id, "ticker": ticker, "report_id": 1}
        return _build(_RecommendationFactory, pins, overrides)

    @staticmethod
    def create_stock_history(ticker: str = "AAPL", days: int = 30) -> Dict[str, Any]:
        """테스트용 주식 히스토리 데이터 생성"""
        from datetime import timedelta

        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        history = {}

        base_price = 150.0
        for i in range(days):
            day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # 간단한 가격 변동 시뮬레이션
            price_change = (i % 5 - 2) * 2  # -4 to +4 범위의 변동
            current_price = base_price + price_change

            history[day] = {
                "Open": round(current_price - 1, 2),
                "High": round(current_price + 2, 2),
                "Low": round(current_price - 2, 2),
                "Close": round(current_price, 2),
                "Volume": 1000000 + (i * 10000),
            }

        return {
            "status": "success",
            "stock_history": {ticker: history},
            "stock_info": {
                ticker: {
                    "symbol": ticker,
                    "shortName": f"{ticker} Inc.",
                    "currentPrice": base_price,
                    "marketCap": 2400000000000,
                }
            },
        }

    @staticmethod
    def create_agent_state(agent_type: str = "crawler", **overrides) -> Dict[str, Any]:
        """테스트용 Agent State 생성"""
        base_data = {
            "asof": datetime.now(timezone.utc).isoformat(),
            "universe": ["AAPL", "MSFT", "GOOGL", "NVDA"],
            "new_candidates": [],
            "messages": [],
        }

        # 에이전트 타입별 특별한 상태 추가
        if agent_type == "momo":
            base_data.update({"momentum_scores": [], "top_movers": []})
        elif agent_type == "fund":
            base_data.update({"fundamental_analysis": [], "financial_metrics": {}})
        elif agent_type == "risk":
            base_data.update({"risk_metrics": {}, "risk_warnings": []})
        elif agent_type == "decider":
            base_data.update({"decisions": [], "rationale": ""})
        elif agent_type == "reporter":
            base_data.update({"report": "", "sections": []})

        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_multiple_users(count: int = 3) -> List[Dict[str, Any]]:
        """여러 사용자 데이터 생성"""
        return [MockDataGenerator.create_user(user_id=i + 1) for i in range(count)]

    @staticmethod
    def create_multiple_portfolios(count: int = 3, user_id: int = 1) -> List[Dict[str, Any]]:
        """여러 포트폴리오 데이터 생성"""
        return [MockDataGenerator.create_portfolio(portfolio_id=i + 1, user_id=user_id) for i in range(count)]

    @staticmethod
    def create_multiple_positions(count: int = 5, portfolio_id: int = 1) -> List[Dict[str, Any]]:
        """여러 포지션 데이터 생성"""
        tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"]
        return [
            MockDataGenerator.create_position(
                position_id=i + 1, portfolio_id=portfolio_id, ticker=tickers[i % len(tickers)]
            )
            for i in range(count)
        ]


# 자주 사용되는 Mock 데이터 상수
SAMPLE_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META", "BRK-B", "AVGO", "WMT"]

SAMPLE_CURRENCIES = ["USD", "KRW", "EUR", "JPY", "GBP"]

SAMPLE_TRANSACTION_TYPES = ["BUY", "SELL"]

SAMPLE_TIMEZONES = ["Asia/Seoul", "America/New_York", "Europe/London", "Asia/Tokyo"]

SAMPLE_LANGUAGES = ["ko", "en", "ja", "zh"]
