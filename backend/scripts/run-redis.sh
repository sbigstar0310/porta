#!/bin/bash

# Exit on error
set -e

# Check Directory is backend
if [ "$(basename "$(pwd)")" != "backend" ]; then
    echo "Error: Directory is not backend"
    exit 1
fi

# Check Redis is already running (Skip if running)
if docker ps | grep -q "redis"; then
    echo "Redis is already running"
    exit 0
fi

# Run Redis
docker run -p 6379:6379 redis