# backend/routers/portfolio.py
from fastapi import APIRouter, Depends, HTTPException
from repo import PortfolioRepo, get_portfolio_repo
from data.schemas import PortfolioOut, PortfolioPatch

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# TODO: 데모에서 인증/다중사용자 붙기 전까지 user_id=1로 고정
CURRENT_USER_ID = 1


@router.get("", response_model=PortfolioOut)
async def get_portfolio(portfolio_repo: PortfolioRepo = Depends(get_portfolio_repo)):
    """현재 사용자의 포트폴리오 조회"""
    try:
        portfolio = await portfolio_repo.get_current_portfolio(user_id=CURRENT_USER_ID)
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Portfolio not found: {str(e)}")


@router.patch("", response_model=PortfolioOut)
async def patch_portfolio(payload: PortfolioPatch, portfolio_repo: PortfolioRepo = Depends(get_portfolio_repo)):
    """포트폴리오 정보 업데이트"""
    try:
        # TODO: PortfolioRepo에 update 메서드 추가 필요
        # 현재는 기본 조회만 반환
        portfolio = await portfolio_repo.get_current_portfolio(user_id=CURRENT_USER_ID)
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Portfolio update failed: {str(e)}")
