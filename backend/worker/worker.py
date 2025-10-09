from celery import Celery
import sys
import os
import logging

logger = logging.getLogger(__name__)

# 현재 디렉토리를 Python 경로에 추가 (graph 모듈 등을 찾기 위해)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__ + "/..")))

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["worker.tasks"],  # 태스크 파일 명시적으로 포함
)

# load config from celeryconfig.py
celery_app.config_from_object("worker.celeryconfig")

# task routes
celery_app.conf.task_routes = {
    "worker.tasks.run_agent_task": {"queue": "agent"},
    "worker.tasks.run_scheduled_agent_task": {"queue": "agent"},
}

celery_app.conf.update(
    # 로깅 설정
    worker_hijack_root_logger=False,  # Celery가 root logger를 하이재킹하지 않도록
    worker_redirect_stdouts_level="INFO",
    # 태스크 추적
    task_track_started=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    # 결과 만료 시간
    task_result_expires=3600,  # 1시간
    # beat 설정
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url="redis://redis:6379/0",
    # timezone 설정
    timezone="UTC",
    enable_utc=True,
)
