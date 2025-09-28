# backend/routers/portfolio.py
from fastapi import APIRouter, Depends, HTTPException
from usecase import PortfolioUsecase, get_portfolio_usecase
from data.schemas import PortfolioOut, PortfolioPatch
from dependencies.auth import get_current_user_id

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioOut)
async def get_portfolio(
    current_user_id: int = Depends(get_current_user_id),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
):
    """현재 사용자의 포트폴리오 조회"""
    try:
        portfolio = await portfolio_usecase.get_current_portfolio(user_id=current_user_id)
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Portfolio not found: {str(e)}")


@router.patch("", response_model=PortfolioOut)
async def patch_portfolio(
    payload: PortfolioPatch,
    current_user_id: int = Depends(get_current_user_id),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
) -> PortfolioOut:
    """포트폴리오 정보 업데이트"""
    try:
        portfolio = await portfolio_usecase.update_portfolio(user_id=current_user_id, portfolio=payload)
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Portfolio update failed: {str(e)}")
