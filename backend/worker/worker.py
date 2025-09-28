from celery import Celery
import sys
import os

# 현재 디렉토리를 Python 경로에 추가 (graph 모듈 등을 찾기 위해)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__ + "/..")))

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["worker.tasks"],  # 태스크 파일 명시적으로 포함
)

celery_app.conf.task_routes = {
    "worker.tasks.run_agent_task": {"queue": "agent"},
}

celery_app.conf.update(
    # Celery가 root logger를 하이재킹하지 않도록
    worker_hijack_root_logger=False,
    # print/stdout 을 어떤 레벨로 보낼지
    worker_redirect_stdouts_level="INFO",
    # 유용한 이벤트/상태
    task_track_started=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
)
