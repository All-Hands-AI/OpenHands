#!/usr/bin/env bash
set -euo pipefail

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
HOST=${HOST:-0.0.0.0}
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

log() { echo -e "[oneclick-server] $*"; }

# 1) Prefer Docker if available
if command -v docker >/dev/null 2>&1 && [ -f "$ROOT_DIR/docker-compose.yml" ]; then
  log "Docker detected. Bringing services up via docker compose..."
  export WORKSPACE_BASE=${WORKSPACE_BASE:-"$ROOT_DIR/workspace"}
  export SANDBOX_USER_ID=${SANDBOX_USER_ID:-"$(id -u)"}
  docker compose up -d --build
  log "Done. Access frontend at: http://localhost:${FRONTEND_PORT} (or server's IP)"
  exit 0
fi

# 2) Native run (no Docker)
log "Docker not available; proceeding with native run."

# Python env via Poetry
if ! command -v poetry >/dev/null 2>&1; then
  log "Poetry not found. Installing locally via pip..."
  python3 -m pip install --user -q poetry
  export PATH="$HOME/.local/bin:$PATH"
fi

log "Installing backend dependencies with Poetry..."
poetry config virtualenvs.create false || true
poetry install --only main -n

# Frontend deps
log "Installing frontend dependencies..."
if ! command -v npm >/dev/null 2>&1; then
  log "npm is required. Please install Node.js (>=22)."; exit 1
fi
pushd frontend >/dev/null
npm ci --no-audit --no-fund
log "Building frontend..."
npm run build
popd >/dev/null

# Logs directory
mkdir -p logs

# Start backend
log "Starting backend on ${HOST}:${BACKEND_PORT}..."
nohup poetry run uvicorn openhands.server.listen:app \
  --host "${HOST}" --port "${BACKEND_PORT}" \
  > logs/backend.log 2>&1 &
BACK_PID=$!

# Start static server for built frontend
log "Starting static server for frontend on ${HOST}:${FRONTEND_PORT}..."
# serve will run in foreground to keep the script attached
npx -y serve@14 -s frontend/build -l "${HOST}:${FRONTEND_PORT}"

# Cleanup on exit
trap 'kill ${BACK_PID} >/dev/null 2>&1 || true' EXIT