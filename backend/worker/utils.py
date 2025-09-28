from celery import Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def update_progress(
    task_instance: Task,
    percent: float,
    message: str,
):
    """진행률 업데이트 헬퍼 함수"""
    try:
        logger.info(f"update_progress 호출됨: {percent:.1f}% - {message}")
        task_instance.update_state(
            state="PROGRESS",
            meta={
                "percent": percent,
                "message": message,
            },
        )
        logger.info(f"update_state 완료: {percent:.1f}% - {message}")
    except Exception as e:
        logger.error(f"update_progress 실패: {e}")
        raise
