from celery.schedules import crontab

beat_schedule = {
    "run-daily-for-user-123": {
        "task": "tasks.run_agent_for_user",
        "schedule": crontab(hour=9, minute=0),  # 매일 오전 9시
        "args": ("user_123",),
    },
}
