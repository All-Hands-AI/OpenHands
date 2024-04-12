#!/bin/bash --login

eval "$(conda shell.bash activate "${VENV_NAME}")"

if [ -n "${DEBUG}" ]; then
    printf "******\n* System information: \n******"
    /bin/bash < "${APP_ROOT}/run/env_debug"
    echo "Python executable in ${VENV_NAME}: $(which python3) v$(python3 --version)"
    echo "Anaconda environments info:"
    conda info --envs
    echo "Anaconda packages sources: $(conda config --show-sources)"
    echo "PYTHONPATH: $(env | grep PYTHONPATH)"
    env | grep LITELLM_PORT
    env | grep JUPYTER_PORT
    echo "Nvidia CUDA properties:"
    nvidia-smi
fi

set -eux

# Start API server
if [ -n "${DEBUG}" ]; then
    python3 oppendevin_launcher --port "${DEVIN_API_PORT}" --reload --log-level info \
    --llm-model mistral:7b \
    --embeddings-model llama2
else
    python3 oppendevin_launcher --port "${DEVIN_API_PORT}" --reload --log-level critical \
    --llm-model mistral:7b \
    --embeddings-model llama2
fi

