from fastapi import APIRouter, Depends, HTTPException, status
from data.schemas import PositionOut, PositionCreate, PositionPatch
from usecase import PositionUsecase, PortfolioUsecase, get_position_usecase, get_portfolio_usecase
from dependencies.auth import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/position", tags=["position"])


async def _get_owned_position(
    position_id: int,
    current_user_id: int,
    position_usecase: PositionUsecase,
    portfolio_usecase: PortfolioUsecase,
) -> PositionOut:
    """포지션을 조회하고 현재 사용자의 포트폴리오 소유인지 검증한다.

    존재하지 않거나 타인 소유면 동일하게 404 — 타인에게 포지션 존재 여부를
    노출하지 않기 위해 403 대신 404를 쓴다.
    """
    position = await position_usecase.get_position(position_id)
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")

    portfolio = await portfolio_usecase.get_current_portfolio(current_user_id)
    if not portfolio or position.portfolio_id != portfolio.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")

    return position


@router.get("/{position_id}", response_model=PositionOut)
async def get_position(
    position_id: int,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
) -> PositionOut:
    return await _get_owned_position(position_id, current_user_id, position_usecase, portfolio_usecase)


@router.post("/", response_model=PositionOut)
async def add_position(
    position: PositionCreate,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
) -> PositionOut:
    # 본인 포트폴리오에만 포지션 추가 가능
    portfolio = await portfolio_usecase.get_current_portfolio(current_user_id)
    if not portfolio or position.portfolio_id != portfolio.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="본인 포트폴리오에만 포지션을 추가할 수 있습니다."
        )

    try:
        created_position = await position_usecase.create_position(position)
        return created_position
    except Exception as e:
        logger.error(f"Error creating position: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating position: {e}")


@router.patch("/{position_id}", response_model=PositionOut)
async def patch_position(
    position_id: int,
    position: PositionPatch,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
) -> PositionOut:
    await _get_owned_position(position_id, current_user_id, position_usecase, portfolio_usecase)

    try:
        updated = await position_usecase.update_position(position_id, position)
        return PositionOut(**updated.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating position: {e}")


@router.delete("/{position_id}")
async def delete_position(
    position_id: int,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
) -> dict:
    await _get_owned_position(position_id, current_user_id, position_usecase, portfolio_usecase)

    try:
        success = await position_usecase.delete_position(position_id)
        return {"success": success, "message": "Position deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting position: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting position: {e}")
