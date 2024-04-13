#!/bin/bash --login

eval "$(conda shell.bash activate "${VENV_NAME}")"

if [ -n "${DEBUG}" ]; then
    echo "Python executable in ${VENV_NAME}': $(which python3) v$(python3 --version)"

    echo "Conda environments info:"
    conda info --envs

    env | grep PYTHONPATH

    echo "Nvidia CUDA properties:"
    nvidia-smi
#     pwd
    bash $BIN_DIR/env_debug
fi

set -eux

# Start API server
if [ -n "${DEBUG}" ]; then
    python3 "${APP_DIR}/devin_up" \
        --port "${DEVIN_API_PORT}" --host "${DEVIN_HOST}" \
        --log-level critical
else
    python3 "${APP_DIR}/devin_up" \
        --port "${DEVIN_API_PORT}" --host "${DEVIN_HOST}" \
        --reload --log-level info
fi

