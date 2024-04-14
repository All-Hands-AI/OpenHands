#!/bin/sh

# Configure defaults
# Run API server

if [ -n "${DEBUG}" ]; then set -eux; fi

PATH="${PATH}:$yarn_global_root/node_modules/npm/bin:$yarn_global_root/bin"

echo "Backend endpoint address http://${DEVIN_HOST}:${DEVIN_API_PORT}"

if [ -n "${SECURE_MODE}" ]; then
    export UI_PORT="${UI_HTTPS_PORT}"
else
    export UI_PORT="${UI_HTTP_PORT}"
fi

if [ -n "${SECURE_MODE}" ]; then
    echo "Starting frontend server on http://0.0.0.0:${UI_PORT}"
    vite --config vite.config.js --host 0.0.0.0 --port "${UI_PORT}"
else
    echo "Starting frontend server on https://0.0.0.0:${UI_PORT}"
    vite --config vite.config.js --host 0.0.0.0 --port "${UI_PORT}" \
        --clearScreen false
fi
