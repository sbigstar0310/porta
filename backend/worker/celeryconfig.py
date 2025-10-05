from celery.schedules import crontab

# static schedule
beat_schedule = {
    # sync schedules
    "sync-schedules": {
        "task": "worker.tasks.sync_all_schedules",
        "schedule": crontab(minute="*/10"),  # 10분마다 동기화
    },
}
