# backend/schemas.py
"""
API 입출력을 위한 스키마 정의
"""
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Literal
from datetime import datetime, date
import re

ISO3 = re.compile(r"^[A-Z]{3}$")


# ============= User Schemas =============


class UserCreate(BaseModel):
    """사용자 생성 스키마"""

    email: Optional[str] = None
    password: Optional[str] = None
    timezone: str = Field(default="Asia/Seoul", max_length=50, description="IANA timezone (예: Asia/Seoul)")
    language: str = Field(default="ko", min_length=2, max_length=2, description="ISO 639-1 언어 코드")

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v):
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v):
        import re

        timezone_pattern = re.compile(r"^[A-Za-z0-9_/+-]+$")
        if not timezone_pattern.match(v):
            raise ValueError("Invalid timezone format")
        return v

    @field_validator("language")
    @classmethod
    def _validate_language(cls, v):
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Language must be a 2-character ISO 639-1 code")
        return v.lower()


class UserOut(BaseModel):
    """사용자 출력 스키마"""

    id: int
    email: Optional[str] = None
    timezone: str
    language: str
    email_verified: bool = Field(default=False, description="이메일 인증 완료 여부")
    created_at: datetime
    updated_at: datetime
    last_login: datetime

    # 인증 토큰들 (로그인 시에만 포함)
    access_token: Optional[str] = Field(None, description="JWT 액세스 토큰")
    refresh_token: Optional[str] = Field(None, description="JWT 리프레시 토큰")
    token_type: Optional[str] = Field(None, description="토큰 타입 (Bearer)")
    expires_in: Optional[int] = Field(None, description="토큰 만료 시간 (초)")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "timezone": "Asia/Seoul",
                "language": "ko",
                "created_at": "2025-01-20T10:30:00Z",
                "updated_at": "2025-01-20T10:30:00Z",
                "last_login": "2025-01-20T10:30:00Z",
            }
        }


class UserPatch(BaseModel):
    """사용자 정보 수정 스키마"""

    email: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50, description="IANA timezone (예: Asia/Seoul)")
    language: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 639-1 언어 코드")

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v):
        if v is None:
            return v
        import re

        timezone_pattern = re.compile(r"^[A-Za-z0-9_/+-]+$")
        if not timezone_pattern.match(v):
            raise ValueError("Invalid timezone format")
        return v

    @field_validator("language")
    @classmethod
    def _validate_language(cls, v):
        if v is None:
            return v
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Language must be a 2-character ISO 639-1 code")
        return v.lower()


# ============= Portfolio Schemas =============


class PortfolioCreate(BaseModel):
    """포트폴리오 생성 스키마"""

    user_id: int
    base_currency: str = Field(default="USD")
    cash: Decimal = Field(default=Decimal("0.00"), ge=0)

    @field_validator("base_currency")
    @classmethod
    def _validate_currency(cls, v):
        if not ISO3.match(v):
            raise ValueError("base_currency must be ISO-4217 like USD/KRW (A-Z,3)")
        return v

    @field_validator("cash")
    @classmethod
    def _quantize_cash(cls, v: Decimal):
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class PortfolioOut(BaseModel):
    """포트폴리오 기본 출력 스키마"""

    id: int
    user_id: int
    base_currency: str
    cash: Decimal
    updated_at: datetime
    positions: List["PositionOut"] = Field(default_factory=list, description="보유 포지션 목록")
    # 실시간 계산 필드들 (옵셔널)
    total_stock_value: Optional[Decimal] = Field(None, description="보유 주식 총 시장가치")
    total_value: Optional[Decimal] = Field(None, description="포트폴리오 총 가치 (현금 + 주식)")
    total_unrealized_pnl: Optional[Decimal] = Field(None, description="총 미실현 손익")
    total_unrealized_pnl_pct: Optional[Decimal] = Field(None, description="총 미실현 손익 비율")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "base_currency": "USD",
                "cash": 1200.00,
                "updated_at": "2025-01-20T10:30:00Z",
                "positions": [
                    {
                        "id": 1,
                        "portfolio_id": 1,
                        "ticker": "AAPL",
                        "total_shares": 10.5,
                        "avg_buy_price": 150.25,
                        "updated_at": "2025-01-20T09:30:00Z",
                        "current_price": 165.50,
                        "current_market_value": 1737.75,
                        "unrealized_pnl": 160.12,
                        "unrealized_pnl_pct": 10.15,
                    }
                ],
                "total_stock_value": 1737.75,
                "total_value": 2937.75,
                "total_unrealized_pnl": 160.12,
                "total_unrealized_pnl_pct": 10.15,
            }
        }


class PortfolioPatch(BaseModel):
    """포트폴리오 부분 수정 스키마"""

    cash: Optional[Decimal] = Field(None, ge=0)
    base_currency: Optional[str] = None

    @field_validator("base_currency")
    @classmethod
    def _validate_currency(cls, v):
        if v is None:
            return v
        if not ISO3.match(v):
            raise ValueError("base_currency must be ISO-4217 like USD/KRW (A-Z,3)")
        return v

    @field_validator("cash")
    @classmethod
    def _quantize_cash(cls, v: Optional[Decimal]):
        if v is None:
            return v
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    class Config:
        json_encoders = {Decimal: float}  # Decimal을 float으로 변환하여 JSON serialization 지원


# ============= Transaction Schemas =============


class TransactionCreate(BaseModel):
    """거래 생성 스키마"""

    portfolio_id: int = Field(..., gt=0)
    ticker: str = Field(..., min_length=1, max_length=10)
    transaction_type: Literal["BUY", "SELL"]
    shares: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    transaction_date: date
    fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD")
    exchange: str = Field(default="")
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("ticker")
    @classmethod
    def _validate_ticker(cls, v):
        return v.upper().strip()

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, v):
        if not ISO3.match(v):
            raise ValueError("currency must be ISO-4217 like USD/KRW (A-Z,3)")
        return v

    @field_validator("shares", "price", "fee")
    @classmethod
    def _quantize_decimal(cls, v: Decimal):
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TransactionOut(BaseModel):
    """거래 출력 스키마"""

    id: int
    portfolio_id: int
    ticker: str
    transaction_type: Literal["BUY", "SELL"]
    shares: Decimal
    price: Decimal
    transaction_date: date
    fee: Decimal
    currency: str
    exchange: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Position Schemas =============


class PositionCreate(BaseModel):
    """포지션 생성 스키마"""

    portfolio_id: int
    ticker: str
    total_shares: Decimal
    avg_buy_price: Decimal

    class Config:
        json_encoders = {Decimal: float}  # Decimal을 float으로 변환하여 JSON serialization 지원


class PositionOut(BaseModel):
    """포지션 출력 스키마"""

    id: int
    portfolio_id: int
    ticker: str
    total_shares: Decimal
    avg_buy_price: Decimal
    updated_at: datetime
    # 계산 필드들 (옵셔널)
    current_price: Optional[Decimal] = None
    current_market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_pct: Optional[Decimal] = None

    class Config:
        from_attributes = True
        json_encoders = {Decimal: float}  # Decimal을 float으로 변환하여 JSON serialization 지원


class PositionPatch(BaseModel):
    """포지션 부분 수정 스키마"""

    ticker: Optional[str] = None
    total_shares: Optional[Decimal] = Field(None, ge=0)
    avg_buy_price: Optional[Decimal] = Field(None, gt=0)

    class Config:
        json_encoders = {Decimal: float}  # Decimal을 float으로 변환하여 JSON serialization 지원


# ============= Stock Schemas =============


class StockSearchOut(BaseModel):
    """종목 검색 결과 스키마"""

    ticker: str = Field(..., min_length=1, max_length=10, description="종목 티커 심볼")
    company_name: str = Field(..., min_length=1, max_length=200, description="회사명")

    @field_validator("ticker")
    @classmethod
    def _validate_ticker(cls, v):
        return v.upper().strip()

    @field_validator("company_name")
    @classmethod
    def _validate_company_name(cls, v):
        return v.strip()

    class Config:
        json_schema_extra = {"example": {"ticker": "AAPL", "company_name": "Apple Inc."}}


# ============= Report Schemas =============


class ReportCreate(BaseModel):
    """보고서 생성 스키마"""

    user_id: int = Field(..., gt=0)
    report_md: str = Field(..., min_length=1, description="마크다운 형식의 보고서 내용")
    language: str = Field(default="ko", min_length=2, max_length=2, description="ISO 639-1 언어 코드")

    @field_validator("language")
    @classmethod
    def _validate_language(cls, v):
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Language must be a 2-character ISO 639-1 code")
        return v.lower()


class ReportOut(BaseModel):
    """보고서 출력 스키마"""

    id: int
    user_id: int
    created_at: datetime
    report_md: str
    language: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "created_at": "2025-09-16T12:30:00Z",
                "report_md": "# 포트폴리오 분석 보고서\n\n## 요약\n귀하의 포트폴리오 분석 결과입니다.",
                "language": "ko",
            }
        }


class ReportPatch(BaseModel):
    """보고서 수정 스키마"""

    report_md: Optional[str] = Field(None, min_length=1, description="마크다운 형식의 보고서 내용")
    language: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 639-1 언어 코드")

    @field_validator("language")
    @classmethod
    def _validate_language(cls, v):
        if v is None:
            return v
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Language must be a 2-character ISO 639-1 code")
        return v.lower()


class TaskProgressOut(BaseModel):
    """
    Celery 태스크 진행 상황 응답 스키마
    """

    task_id: str
    status: str  # PENDING, PROGRESS, SUCCESS, FAILURE, REVOKED
    percent: float  # 0.0 ~ 100.0
    message: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
