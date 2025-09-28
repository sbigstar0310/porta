# backend/main.py
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import os
from data.db import Database
from routers.portfolio import router as portfolio_router
from routers.health import router as health_router
from routers.user import router as user_router
from routers.auth import router as auth_router
from routers.agent import router as agent_router
import logging
import colorlog


# 색상 로깅 설정
def setup_colored_logging():
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)s] %(name)s\t%(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


# 기존 로깅 설정 대신 사용
logger = setup_colored_logging()

# 환경변수 로드
load_dotenv()

# API KEYS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 라이프사이클 관리
    시작과 종료 시 필요한 초기화/정리 로직을 처리합니다.
    """
    # 시작 시
    try:
        # 데이터베이스 초기화
        await Database.initialize()
        yield
    except Exception as e:
        logger.error(f"앱 초기화 실패: {e}")
        raise
    finally:
        # 종료 시
        logger.info("앱 종료 처리 중...")
        db = Database()
        await db.close()
        logger.info("앱 종료 완료")


app = FastAPI(title="PORTA", lifespan=lifespan)

# 라우터 등록
app.include_router(portfolio_router)
app.include_router(health_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(agent_router)
