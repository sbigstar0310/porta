from fastapi import APIRouter, Depends, HTTPException, status
from data.schemas import PositionOut, PositionCreate, PositionPatch
from usecase import PositionUsecase, get_position_usecase
from dependencies.auth import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/position", tags=["position"])


@router.get("/{position_id}", response_model=PositionOut)
async def get_position(
    position_id: int,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
) -> PositionOut:
    # TODO: position이 current_user의 portfolio에 속하는지 검증 필요
    try:
        position = await position_usecase.get_position(position_id)
        return PositionOut(**position.model_dump())
    except Exception as e:
        logger.error(f"Error getting position: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error getting position: {e}")


@router.post("/", response_model=PositionOut)
async def add_position(
    position: PositionCreate,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
) -> PositionOut:
    # TODO: position.portfolio_id가 current_user의 portfolio인지 검증 필요
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
) -> PositionOut:
    # TODO: position이 current_user의 portfolio에 속하는지 검증 필요
    try:
        position = await position_usecase.update_position(position_id, position)
        return PositionOut(**position.model_dump())
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating position: {e}")


@router.delete("/{position_id}", response_model=PositionOut)
async def delete_position(
    position_id: int,
    current_user_id: int = Depends(get_current_user_id),  # 인증 필요
    position_usecase: PositionUsecase = Depends(get_position_usecase),
) -> PositionOut:
    # TODO: position이 current_user의 portfolio에 속하는지 검증 필요
    try:
        position = await position_usecase.delete_position(position_id)
        return PositionOut(**position.model_dump())
    except Exception as e:
        logger.error(f"Error deleting position: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting position: {e}")
