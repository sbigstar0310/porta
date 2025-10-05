class Constants:
    SCHEDULED_AGENT_TASK = "worker.tasks.run_scheduled_agent_task"
    USER_SCHEDULE_KEY_PREFIX = "user-"

    # Retry 정책 상수
    DEFAULT_RETRY_POLICY = {
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.2,
    }

    # task 보정 시간
    TASK_CORRECTION_TIME = 30
