#!/bin/bash

# Exit on error
set -e

echo "[STARTUP] Waiting for database at $POSTGRES_SERVER..."
# Simple wait loop (postgres image might take a few seconds)
sleep 5

echo "[STARTUP] Running Migrations..."
alembic upgrade head

echo "[STARTUP] Seeding Initial Data..."
python -m app.initial_data

echo "[STARTUP] Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
