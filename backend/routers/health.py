# backend/routers/health.py
from fastapi import APIRouter
from data.db import Database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    """기본 헬스체크 엔드포인트"""
    return {"ok": True}


@router.get("/db")
async def health_db():
    """데이터베이스 헬스체크 엔드포인트"""
    try:
        db = Database()
        health_status = await db.health_check()
        return health_status
    except Exception as e:
        logger.error(f"DB 헬스체크 실패: {e}")
        return {"status": "error", "connected": False, "error": str(e)}
