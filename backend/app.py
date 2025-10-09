# backend/main.py
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from data.db import Database
from routers.portfolio import router as portfolio_router
from routers.health import router as health_router
from routers.user import router as user_router
from routers.auth import router as auth_router
from routers.agent import router as agent_router
from routers.position import router as position_router
from routers.stock import router as stock_router
from routers.report import router as report_router
from routers.schedule import router as schedule_router
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

    # 루트 로거에 핸들러를 추가하여 모든 모듈의 로그가 출력되도록 설정
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # 앱별 로거도 설정
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    return logger


# 기존 로깅 설정 대신 사용
logger = setup_colored_logging()

# 환경변수 로드
# Docker 환경에서는 env_file로 환경변수가 자동 로드되므로 .env 파일 로드는 선택사항
result = load_dotenv(dotenv_path="../.env")
if not result:
    # Docker 환경에서는 env_file로 환경변수가 로드되므로 경고만 출력
    logger.warning(".env 파일을 찾을 수 없습니다. Docker env_file 설정을 사용합니다.")
else:
    logger.info(".env 파일이 성공적으로 로드되었습니다.")


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

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(portfolio_router)
app.include_router(health_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(position_router)
app.include_router(stock_router)
app.include_router(report_router)
app.include_router(schedule_router)
