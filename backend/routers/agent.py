# backend/routers/agent.py
from fastapi import APIRouter, Depends, HTTPException
from usecase import (
    PortfolioUsecase,
    get_portfolio_usecase,
    ReportUsecase,
    get_report_usecase,
    UserUsecase,
    get_user_usecase,
    TaskUsecase,
    get_task_usecase,
)
from graph.app import run_graph
from dependencies.auth import get_current_user_id
from clients import get_email_client, EmailClient
from worker.tasks import run_agent_task
from data.schemas import TaskProgressOut
import logging

router = APIRouter(prefix="/agent", tags=["agent"])

logger = logging.getLogger(__name__)


@router.post("/run-worker")
async def agent_run_worker(
    current_user_id: int = Depends(get_current_user_id),
    task_usecase: TaskUsecase = Depends(get_task_usecase),
) -> dict:
    try:
        # 1. 해당 유저의 실행 중인 태스크가 있는지 확인
        existing_task = task_usecase.check_existing_running_task(current_user_id)
        if existing_task["is_running"]:
            return {
                "message": "Agent is already running for this user",
                "task_id": existing_task["task_id"],
                "status": "ALREADY_RUNNING",
            }

        # 3. 새 태스크 시작 (args가 제대로 추적되도록)
        task = run_agent_task.apply_async(args=(current_user_id,), queue="agent")  # args로 명시적 전달

        logger.info(f"Started new agent task for user {current_user_id}: {task.id}")
        return {"message": "Agent run started", "task_id": task.id, "status": "STARTED"}
    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_progress(
    task_id: str,
    current_user_id: int = Depends(get_current_user_id),
    task_usecase: TaskUsecase = Depends(get_task_usecase),
) -> TaskProgressOut:
    """
    Celery 태스크의 진행 상황을 조회합니다.

    Returns:
        TaskProgressResponse: 태스크 진행 상황
    """
    try:
        result = task_usecase.get_task_progress(task_id)
        return result

    except Exception as e:
        logger.error(f"태스크 진행 상황 조회 실패 (task_id: {task_id}): {e}")
        raise HTTPException(status_code=500, detail=f"태스크 상태 조회 실패: {str(e)}")


@router.delete("/task/{task_id}")
async def cancel_task(
    task_id: str,
    current_user_id: int = Depends(get_current_user_id),
    task_usecase: TaskUsecase = Depends(get_task_usecase),
) -> dict:
    try:
        result = task_usecase.cancel_task(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다.")
        return {"message": "태스크가 취소되었습니다."}
    except Exception as e:
        logger.error(f"태스크 취소 실패 (task_id: {task_id}): {e}")
        raise HTTPException(status_code=500, detail=f"태스크 취소 실패: {str(e)}")


@router.post("/run")
async def agent_run(
    current_user_id: int = Depends(get_current_user_id),
    email_client: EmailClient = Depends(get_email_client),
    portfolio_usecase: PortfolioUsecase = Depends(get_portfolio_usecase),
    report_usecase: ReportUsecase = Depends(get_report_usecase),
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> dict:
    try:
        portfolio = await portfolio_usecase.get_current_portfolio(user_id=current_user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Get user
        user = user_usecase.get_user_profile(user_id=current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 에이전트 실행
        result = run_graph(portfolio=portfolio, user_id=current_user_id, language=user.language)
        logging.info(f"Agent run result: {result}")

        # 에이전트 보고서 결과 저장
        report_md = result.get("report_md", "NO REPORT")
        report = await report_usecase.create_report(
            user_id=current_user_id,
            report_md=report_md,
            language="ko",
        )
        logger.info(f"Agent report saved: {report}")

        # 에이전트 보고서 결과 이메일 전송
        response = email_client.send_markdown_email_with_pdf(
            to=user.email,
            subject="[Porta] 에이전트 보고서 결과",
            markdown_content=report_md,
        )
        logger.info(f"Agent email sent: {response}")

        return result
    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

