#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# One-click Termux launcher using proot-distro (Ubuntu)
DISTRO=ubuntu
APP_DIR=/root/app
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
HOST=${HOST:-0.0.0.0}

log(){ echo -e "[oneclick-termux] $*"; }

# Ensure proot-distro
if ! command -v proot-distro >/dev/null 2>&1; then
  pkg update -y && pkg install -y proot-distro
fi

# Install Ubuntu
if ! proot-distro list | grep -q "^${DISTRO} "; then
  proot-distro install ${DISTRO}
fi

# Copy project into the distro if not present
proot-distro login ${DISTRO} -- /bin/bash -lc "mkdir -p ${APP_DIR}"
rsync -a --delete --exclude 'node_modules' --exclude '.venv' --exclude '.git' ./ $(proot-distro login ${DISTRO} -- /bin/bash -lc 'pwd') >/dev/null 2>&1 || true

# Bootstrap inside distro
proot-distro login ${DISTRO} -- /bin/bash -lc "\
  set -euo pipefail; \
  apt update -y && apt install -y git make build-essential python3 python3-venv python3-pip nodejs npm netcat; \
  cd ${APP_DIR} || exit 1; \
  python3 -m pip install --upgrade pip; \
  pip install poetry; \
  poetry config virtualenvs.create false || true; \
  poetry install --only main -n; \
  cd frontend && npm ci --no-audit --no-fund && npm run build; \
  cd ${APP_DIR}; \
  mkdir -p logs; \
  nohup poetry run uvicorn openhands.server.listen:app --host ${HOST} --port ${BACKEND_PORT} > logs/backend.log 2>&1 & \
  npx -y serve@14 -s frontend/build -l ${HOST}:${FRONTEND_PORT} \
"