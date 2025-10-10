#!/bin/bash

# Exit on error
set -e

# Check Directory is backend
if [ "$(basename "$(pwd)")" != "backend" ]; then
    echo "Error: Directory is not backend"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# 로컬 개발 환경용 Redis URL 설정 (환경 변수가 없는 경우)
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}

echo "Using Redis URL: $REDIS_URL"

# Run Celery Beat with RedBeat scheduler and shorter poll interval
celery -A worker.worker.celery_app beat -S redbeat.RedBeatScheduler --loglevel=DEBUG --max-interval=10