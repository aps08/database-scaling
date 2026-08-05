#!/bin/sh
set -e

echo "[start.sh] Executing database schema migrations across all shard nodes..."
uv run alembic upgrade head

echo "[start.sh] Database migrations complete! Starting FastAPI web server..."
exec uv run fastapi run src/main.py --host 0.0.0.0 --port 8000
