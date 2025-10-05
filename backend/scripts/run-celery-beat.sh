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

# Run Celery Beat with RedBeat scheduler and shorter poll interval
celery -A worker.worker.celery_app beat -S redbeat.RedBeatScheduler --loglevel=DEBUG --max-interval=10