from worker.worker import celery_app
from clients import get_email_client
from usecase import get_user_usecase, get_portfolio_usecase, get_report_usecase
from dotenv import load_dotenv
from celery.utils.log import get_task_logger
from celery import Task
import asyncio

logger = get_task_logger(__name__)


async def _initialize_dependencies():
    from data.db import Database

    load_dotenv()
    await Database.initialize()

    email_client = get_email_client()
    portfolio_usecase = get_portfolio_usecase()
    report_usecase = get_report_usecase()
    user_usecase = get_user_usecase()
    return email_client, portfolio_usecase, report_usecase, user_usecase


async def _run_agent_async(
    task_instance: Task,
    current_user_id: int,
):
    """
    Langraph agent 실행

    Args:
        current_user_id: 사용자 ID
    """
    from graph.app import run_graph
    from worker.utils import update_progress

    # Initialize dependencies
    try:
        update_progress(task_instance, 0.0, "의존성 초기화")
        email_client, portfolio_usecase, report_usecase, user_usecase = await _initialize_dependencies()
        update_progress(task_instance, 5.0, "의존성 초기화 완료")
    except Exception as e:
        logger.error(f"Error initializing clients and usecases: {e}")
        raise

    try:
        logger.info(f"Starting agent task for user {current_user_id}")

        # 1. 포트폴리오 조회
        update_progress(task_instance, 10.0, "포트폴리오 조회 중...")
        portfolio = await portfolio_usecase.get_current_portfolio(user_id=current_user_id)
        if not portfolio:
            raise Exception("Portfolio not found")

        # 2. 유저 정보
        update_progress(task_instance, 12.0, "사용자 정보 조회 중...")
        user = user_usecase.get_user_profile(user_id=current_user_id)
        if not user:
            raise Exception("User not found")

        # 3. Langraph 실행
        update_progress(task_instance, 15.0, "에이전트 파이프라인 실행 중...")
        result = run_graph(portfolio=portfolio, user_id=current_user_id, language=user.language)
        logger.info(f"Agent run result: {result}")
        update_progress(task_instance, 90.0, "에이전트 실행 완료")

        # 4. 보고서 저장
        update_progress(task_instance, 95.0, "보고서 저장 중...")
        report_md = result.get("report_md", "NO REPORT")
        report = await report_usecase.create_report(
            user_id=current_user_id,
            report_md=report_md,
            language="ko",
        )
        logger.info(f"Agent report saved: {report}")

        # 5. 이메일 전송
        update_progress(task_instance, 98.0, "이메일 전송 중...")
        response = email_client.send_markdown_email_with_pdf(
            to=user.email,
            subject="[Porta] 에이전트 보고서 결과",
            markdown_content=report_md,
        )
        logger.info(f"Agent email sent: {response}")
        update_progress(task_instance, 100.0, "완료")

        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise


@celery_app.task(bind=True)
def run_agent_task(self: Task, current_user_id: int):
    try:
        return asyncio.run(_run_agent_async(self, current_user_id))
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise
