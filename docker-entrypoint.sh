#!/bin/bash
set -e

mkdir -p /tmp
echo "Initialising database and seeding data..."
python3 /app/seed_on_startup.py

echo "Starting API server..."
exec python -m uvicorn src.api.app:create_app \
    --factory \
    --host "${API_HOST:-0.0.0.0}" \
    --port "${API_PORT:-8000}" \
    --workers "${API_WORKERS:-1}" \
    --log-level "${LOG_LEVEL:-info}"
