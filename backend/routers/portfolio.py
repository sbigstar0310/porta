# backend/routers/portfolio.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from db import get_session, engine, Base, Settings
from models import User, Portfolio
from schemas import PortfolioOut, PortfolioPatch

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
settings = Settings()

# 데모: 인증/다중사용자 붙기 전까지 user_id=1로 고정
CURRENT_USER_ID = 1


async def seed_if_needed(session: AsyncSession):
    # 유저 1 및 포트폴리오가 없으면 생성
    res = await session.execute(select(User).where(User.id == CURRENT_USER_ID))
    user = res.scalar_one_or_none()
    if not user:
        user = User(id=CURRENT_USER_ID, email=None)
        session.add(user)
        await session.flush()
    res = await session.execute(
        select(Portfolio).where(Portfolio.user_id == CURRENT_USER_ID)
    )
    pf = res.scalar_one_or_none()
    if not pf:
        pf = Portfolio(
            user_id=CURRENT_USER_ID,
            base_currency=settings.default_base_currency,
            cash=Decimal("0.00"),
        )
        session.add(pf)
        await session.commit()


@router.get("", response_model=PortfolioOut)
async def get_portfolio(session: AsyncSession = Depends(get_session)):
    await seed_if_needed(session)
    res = await session.execute(
        select(Portfolio).where(Portfolio.user_id == CURRENT_USER_ID)
    )
    pf = res.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return PortfolioOut(
        user_id=CURRENT_USER_ID, base_currency=pf.base_currency, cash=pf.cash
    )


@router.patch("", response_model=PortfolioOut)
async def patch_portfolio(
    payload: PortfolioPatch, session: AsyncSession = Depends(get_session)
):
    await seed_if_needed(session)
    res = await session.execute(
        select(Portfolio).where(Portfolio.user_id == CURRENT_USER_ID)
    )
    pf = res.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if payload.base_currency is not None:
        pf.base_currency = payload.base_currency
    if payload.cash is not None:
        if payload.cash < 0:
            raise HTTPException(status_code=400, detail="cash must be >= 0")
        pf.cash = payload.cash

    await session.commit()
    await session.refresh(pf)
    return PortfolioOut(
        user_id=CURRENT_USER_ID, base_currency=pf.base_currency, cash=pf.cash
    )
