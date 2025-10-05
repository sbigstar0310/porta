from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from usecase import get_schedule_usecase
from usecase.schedule_usecase import (
    ScheduleUsecase,
    ScheduleAlreadyExistsException,
    ScheduleNotFoundOrUnauthorizedException,
)
from data.schemas import ScheduleOut, ScheduleCreate, SchedulePatch
from dependencies.auth import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user_id: int = Depends(get_current_user_id),
    schedule_usecase: ScheduleUsecase = Depends(get_schedule_usecase),
) -> ScheduleOut:
    """
    새로운 스케줄 생성
    사용자당 하나의 스케줄만 생성 가능합니다.
    """
    try:
        # 요청한 사용자 ID와 스키마의 user_id가 일치하는지 확인
        if schedule_data.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="다른 사용자의 스케줄을 생성할 수 없습니다."
            )

        schedule = await schedule_usecase.create_schedule(
            user_id=schedule_data.user_id,
            hour=schedule_data.hour,
            minute=schedule_data.minute,
            timezone=schedule_data.timezone,
            enabled=schedule_data.enabled,
        )
        return schedule

    except ScheduleAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"스케줄 생성 실패: user_id={current_user_id}, error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="스케줄 생성에 실패했습니다.")


@router.get("/me", response_model=Optional[ScheduleOut])
async def get_my_schedule(
    current_user_id: int = Depends(get_current_user_id),
    schedule_usecase: ScheduleUsecase = Depends(get_schedule_usecase),
) -> Optional[ScheduleOut]:
    """
    현재 사용자의 스케줄 조회
    """
    try:
        schedule = await schedule_usecase.get_user_schedule(current_user_id)
        return schedule
    except Exception as e:
        logger.error(f"스케줄 조회 실패: user_id={current_user_id}, error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="스케줄 조회에 실패했습니다.")


@router.get("/{schedule_id}", response_model=ScheduleOut)
async def get_schedule(
    schedule_id: int,
    current_user_id: int = Depends(get_current_user_id),
    schedule_usecase: ScheduleUsecase = Depends(get_schedule_usecase),
) -> ScheduleOut:
    """
    특정 스케줄 조회 (권한 확인 포함)
    """
    try:
        schedule = await schedule_usecase.get_schedule_by_id(schedule_id, current_user_id)
        return schedule

    except ScheduleNotFoundOrUnauthorizedException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"스케줄 조회 실패: schedule_id={schedule_id}, user_id={current_user_id}, error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="스케줄 조회에 실패했습니다.")


@router.patch("/me", response_model=ScheduleOut)
async def update_my_schedule(
    schedule_data: SchedulePatch,
    current_user_id: int = Depends(get_current_user_id),
    schedule_usecase: ScheduleUsecase = Depends(get_schedule_usecase),
) -> ScheduleOut:
    """
    현재 사용자의 스케줄 업데이트
    """
    try:
        schedule = await schedule_usecase.update_schedule(
            user_id=current_user_id,
            hour=schedule_data.hour,
            minute=schedule_data.minute,
            timezone=schedule_data.timezone,
            enabled=schedule_data.enabled,
        )

        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="업데이트할 스케줄이 없습니다.")

        return schedule

    except ScheduleNotFoundOrUnauthorizedException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"스케줄 업데이트 실패: user_id={current_user_id}, error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="스케줄 업데이트에 실패했습니다.")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_schedule(
    current_user_id: int = Depends(get_current_user_id),
    schedule_usecase: ScheduleUsecase = Depends(get_schedule_usecase),
):
    """
    현재 사용자의 스케줄 삭제
    """
    try:
        await schedule_usecase.delete_schedule(current_user_id)

    except ScheduleNotFoundOrUnauthorizedException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"스케줄 삭제 실패: user_id={current_user_id}, error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="스케줄 삭제에 실패했습니다.")
