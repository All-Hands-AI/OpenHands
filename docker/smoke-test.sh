#!/usr/bin/env bash
# Start an agent-canvas image with no mounts and fail unless the unified
# entry point (static-server on :8000, proxying /health to the agent-server)
# answers and the container is still up after a stability window.
#
# A unit test cannot catch a module that exists in scripts/ but was never
# copied into the image (#18342): the frontend dies on startup and the
# entrypoint takes the whole container down with it.
#
# Usage: docker/smoke-test.sh <image> [host-port]
set -euo pipefail

IMAGE="${1:?usage: docker/smoke-test.sh <image> [host-port]}"
PORT="${2:-8000}"
READY_TIMEOUT="${SMOKE_READY_TIMEOUT:-300}"
STABLE_SECONDS="${SMOKE_STABLE_SECONDS:-30}"
NAME="agent-canvas-smoke-$$"
HEALTH_URL="http://127.0.0.1:${PORT}/health"

cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then
    echo "--- last 60 lines of container logs ---"
    docker logs --tail 60 "$NAME" 2>&1 || true
  fi
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

fail() {
  echo "::error::Smoke test failed for ${IMAGE}: $*"
  exit 1
}

running() {
  [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = "true" ]
}

docker run -d --name "$NAME" -p "127.0.0.1:${PORT}:8000" "$IMAGE" >/dev/null
echo "Started ${IMAGE}; waiting up to ${READY_TIMEOUT}s for ${HEALTH_URL}"

deadline=$((SECONDS + READY_TIMEOUT))
until curl -fs -o /dev/null --max-time 5 "$HEALTH_URL"; do
  running || fail "container exited before serving :8000"
  [ "$SECONDS" -lt "$deadline" ] || fail "no healthy response within ${READY_TIMEOUT}s"
  sleep 2
done
echo "Healthy after ${SECONDS}s; checking it stays up for ${STABLE_SECONDS}s"

stable_until=$((SECONDS + STABLE_SECONDS))
while [ "$SECONDS" -lt "$stable_until" ]; do
  running || fail "container exited after becoming healthy"
  sleep 2
done
curl -fsS -o /dev/null --max-time 5 "$HEALTH_URL" ||
  fail "${HEALTH_URL} stopped answering"

echo "Smoke test passed for ${IMAGE}"
