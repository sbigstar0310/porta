from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from usecase import get_report_usecase
from usecase.report_usecase import ReportUsecase
from data.schemas import ReportOut, ReportPatch
from dependencies.auth import get_current_user_id

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    payload: dict,  # {"report_md": str, "language"?: str}
    current_user_id: int = Depends(get_current_user_id),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
) -> ReportOut:
    """보고서 생성"""
    try:
        report_md = payload.get("report_md")
        if not report_md:
            raise HTTPException(status_code=400, detail="report_md is required")

        language = payload.get("language", "ko")

        report = await report_usecase.create_report(user_id=current_user_id, report_md=report_md, language=language)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report creation failed: {str(e)}")


@router.get("/latest", response_model=Optional[ReportOut])
async def get_latest_report(
    current_user_id: int = Depends(get_current_user_id),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
) -> Optional[ReportOut]:
    """최신 보고서 조회"""
    try:
        report = await report_usecase.get_latest_report(user_id=current_user_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Latest report retrieval failed: {str(e)}")


@router.get("", response_model=dict)
async def get_reports(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1-100)"),
    order_by: str = Query("created_at", description="정렬 기준 필드"),
    desc: bool = Query(True, description="내림차순 정렬 여부"),
    current_user_id: int = Depends(get_current_user_id),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
) -> dict:
    """사용자별 보고서 목록 조회 (페이지네이션)"""
    try:
        result = await report_usecase.get_user_reports(
            user_id=current_user_id, page=page, page_size=page_size, order_by=order_by, desc=desc
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reports retrieval failed: {str(e)}")


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: int,
    current_user_id: int = Depends(get_current_user_id),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
) -> ReportOut:
    """보고서 조회"""
    try:
        report = await report_usecase.get_report(report_id=report_id, user_id=current_user_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report retrieval failed: {str(e)}")


@router.patch("/{report_id}", response_model=ReportOut)
async def update_report(
    report_id: int,
    payload: ReportPatch,
    current_user_id: int = Depends(get_current_user_id),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
) -> ReportOut:
    """보고서 수정"""
    try:
        report = await report_usecase.update_report(report_id=report_id, user_id=current_user_id, schema=payload)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report update failed: {str(e)}")


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: int,
    current_user_id: int = Depends(get_current_user_id),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
):
    """보고서 삭제"""
    try:
        success = await report_usecase.delete_report(report_id=report_id, user_id=current_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report deletion failed: {str(e)}")
