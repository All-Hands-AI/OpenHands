#!/bin/bash --login

if [ -n "${DEBUG}" ]; then set -eux; fi

PATH="${PATH}:$yarn_global_root/node_modules/npm/bin:$yarn_global_root/bin"

# pwd

# echo ${PATH}

source ${BIN_DIR/env_debug} | bash

# yarn install

ls -al . | grep node_modules


if [ -n "${DEBUG}" ]; then
    vite --config vite.config.js --host 0.0.0.0 --port "${UI_HTTP_PORT:?}" \
        --clearScreen false --debug True
else
    vite --config vite.config.js --host 0.0.0.0 --port "${UI_HTTP_PORT:?}"
fi
