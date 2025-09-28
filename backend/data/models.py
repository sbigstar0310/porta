# backend/models.py
"""
데이터베이스 테이블과 1:1 대응되는 기본 모델 정의
SQLAlchemy ORM과 연동하기 위한 순수 데이터 모델
"""
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Optional, Literal
import re

ISO3 = re.compile(r"^[A-Z]{3}$")
ISO639_1 = re.compile(r"^[a-z]{2}$")
TIMEZONE_PATTERN = re.compile(r"^[A-Za-z0-9_/+-]+$")


# ============= User Model =============


class User(BaseModel):
    """사용자 테이블 모델 (users)"""

    id: int
    uuid: Optional[str] = None
    email: Optional[str] = None
    timezone: str = Field(default="Asia/Seoul", max_length=50)
    language: str = Field(default="ko", min_length=2, max_length=2)
    email_verified: bool = Field(default=False, description="이메일 인증 완료 여부")

    created_at: datetime
    updated_at: datetime
    last_login: datetime

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v):
        if not TIMEZONE_PATTERN.match(v):
            raise ValueError("Invalid timezone format")
        return v

    @field_validator("language")
    @classmethod
    def _validate_language(cls, v):
        if not ISO639_1.match(v):
            raise ValueError("Language must be a 2-character ISO 639-1 code")
        return v.lower()

    class Config:
        from_attributes = True


# ============= Portfolio Model =============


class Portfolio(BaseModel):
    """포트폴리오 테이블 모델 (portfolios)"""

    id: int
    user_id: int
    base_currency: str = Field(default="USD")
    cash: Decimal = Field(default=Decimal("0.00"), ge=0)
    updated_at: datetime

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

    class Config:
        from_attributes = True


# ============= Transaction Model =============


class Transaction(BaseModel):
    """거래 기록 테이블 모델 (transactions)"""

    id: int
    portfolio_id: int
    ticker: str = Field(..., min_length=1, max_length=10)
    transaction_type: Literal["BUY", "SELL"]
    shares: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    transaction_date: date
    fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD")
    exchange: str = Field(default="", description="거래소 이름")
    notes: Optional[str] = Field(None, max_length=500, description="The notes of the transaction")
    created_at: datetime

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

    class Config:
        from_attributes = True


# ============= Position Model =============


class Position(BaseModel):
    """포지션 테이블 모델 (positions)"""

    id: int
    portfolio_id: int
    ticker: str = Field(..., min_length=1, max_length=10)
    total_shares: Decimal = Field(..., ge=0)
    avg_buy_price: Decimal = Field(..., gt=0)
    updated_at: datetime

    @field_validator("ticker")
    @classmethod
    def _validate_ticker(cls, v):
        return v.upper().strip()

    @field_validator("total_shares", "avg_buy_price")
    @classmethod
    def _quantize_decimal(cls, v: Decimal):
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    class Config:
        from_attributes = True


# ============= Report Model =============


class Report(BaseModel):
    """보고서 테이블 모델 (reports)"""

    id: int
    user_id: int
    created_at: datetime
    report_md: str
    language: str = Field(default="ko")

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v):
        return v

    class Config:
        from_attributes = True
