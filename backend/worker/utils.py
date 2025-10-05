from celery import Task
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except Exception:
    from pytz import timezone as ZoneInfo


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


def to_crontab(time_config: dict) -> crontab:
    """
    시간 설정을 crontab 객체로 변환
    사용자 타임존의 시간을 UTC로 변환하여 저장

    Args:
        time_config: {"hour": int, "minute": int, "timezone": str}

    Returns:
        crontab: Celery crontab 스케줄 객체 (UTC 기준)
    """
    hour = time_config["hour"]
    minute = time_config["minute"]
    user_tz_str = time_config.get("timezone", "UTC")

    # 사용자 타임존의 시간을 UTC로 변환
    # 임의의 날짜를 사용 (시간만 변환하면 되므로)
    from datetime import date

    user_tz = ZoneInfo(user_tz_str)
    utc_tz = ZoneInfo("UTC")

    # 고정된 날짜(2025-01-01)를 사용하여 시간만 변환
    dummy_date = date(2025, 1, 1)
    user_time = datetime.combine(dummy_date, datetime.min.time().replace(hour=hour, minute=minute))
    user_time = user_time.replace(tzinfo=user_tz)
    utc_time = user_time.astimezone(utc_tz)

    return crontab(
        hour=utc_time.hour,
        minute=utc_time.minute,
    )
