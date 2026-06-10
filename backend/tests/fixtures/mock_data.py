# tests/fixtures/mock_data.py
"""
테스트용 Mock 데이터 생성기
"""
from datetime import datetime, timezone
from typing import Dict, List, Any
from decimal import Decimal


class MockDataGenerator:
    """테스트용 Mock 데이터 생성 클래스"""

    @staticmethod
    def create_user(user_id: int = 1, **overrides) -> Dict[str, Any]:
        """테스트용 사용자 데이터 생성"""
        base_data = {
            "id": user_id,
            "uuid": f"test-uuid-{user_id}",
            "email": f"test{user_id}@example.com",
            "timezone": "Asia/Seoul",
            "language": "ko",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc),
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_portfolio(portfolio_id: int = 1, user_id: int = 1, **overrides) -> Dict[str, Any]:
        """테스트용 포트폴리오 데이터 생성"""
        base_data = {
            "id": portfolio_id,
            "user_id": user_id,
            "name": f"테스트 포트폴리오 {portfolio_id}",
            "description": f"테스트용 포트폴리오 {portfolio_id}번입니다",
            "total_value": Decimal("10000.00"),
            "currency": "USD",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_position(
        position_id: int = 1, portfolio_id: int = 1, symbol: str = "AAPL", **overrides
    ) -> Dict[str, Any]:
        """테스트용 포지션 데이터 생성"""
        shares = overrides.get("shares", Decimal("10.0"))
        current_price = overrides.get("current_price", Decimal("155.00"))
        average_price = overrides.get("average_price", Decimal("150.00"))

        base_data = {
            "id": position_id,
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "shares": shares,
            "average_price": average_price,
            "current_price": current_price,
            "market_value": shares * current_price,
            "unrealized_gain_loss": shares * (current_price - average_price),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_transaction(
        transaction_id: int = 1, portfolio_id: int = 1, symbol: str = "AAPL", **overrides
    ) -> Dict[str, Any]:
        """테스트용 거래 데이터 생성"""
        shares = overrides.get("shares", Decimal("10.0"))
        price = overrides.get("price", Decimal("150.00"))

        base_data = {
            "id": transaction_id,
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "transaction_type": "buy",
            "shares": shares,
            "price": price,
            "total_amount": shares * price,
            "transaction_date": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
        }
        base_data.update(overrides)
        return base_data

    @staticmethod
    def create_stock_history(symbol: str = "AAPL", days: int = 30) -> Dict[str, Any]:
        """테스트용 주식 히스토리 데이터 생성"""
        from datetime import timedelta

        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        history = {}

        base_price = 150.0
        for i in range(days):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # 간단한 가격 변동 시뮬레이션
            price_change = (i % 5 - 2) * 2  # -4 to +4 범위의 변동
            current_price = base_price + price_change

            history[date] = {
                "Open": round(current_price - 1, 2),
                "High": round(current_price + 2, 2),
                "Low": round(current_price - 2, 2),
                "Close": round(current_price, 2),
                "Volume": 1000000 + (i * 10000),
            }

        return {
            "status": "success",
            "stock_history": {symbol: history},
            "stock_info": {
                symbol: {
                    "symbol": symbol,
                    "shortName": f"{symbol} Inc.",
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
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN"]
        return [
            MockDataGenerator.create_position(
                position_id=i + 1, portfolio_id=portfolio_id, symbol=symbols[i % len(symbols)]
            )
            for i in range(count)
        ]


# 자주 사용되는 Mock 데이터 상수
SAMPLE_TICKERS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META", "BRK-B", "AVGO", "WMT"]

SAMPLE_CURRENCIES = ["USD", "KRW", "EUR", "JPY", "GBP"]

SAMPLE_TRANSACTION_TYPES = ["buy", "sell"]

SAMPLE_TIMEZONES = ["Asia/Seoul", "America/New_York", "Europe/London", "Asia/Tokyo"]

SAMPLE_LANGUAGES = ["ko", "en", "ja", "zh"]
