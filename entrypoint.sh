#!/bin/bash
set -eo pipefail

echo "starting backend..."
poetry run uvicorn opendevin.server.listen:app --port 3000 --host 0.0.0.0 &

echo "starting frontend..."
cd frontend
npm run start -- --host 0.0.0.0
