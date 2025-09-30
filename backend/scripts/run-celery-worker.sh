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

# Run Celery Worker
celery -A worker.worker.celery_app worker --loglevel=info -Q agent