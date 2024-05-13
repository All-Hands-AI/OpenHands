#!/bin/bash --login

eval "$(conda shell.bash activate "${VENV_NAME}")"

if [ -n "${DEBUG}" ] || [ -n "${DEV_MODE}" ]; then
    set -eux
    printf "******\n* System information: \n******"
    /bin/bash < "${APP_ROOT}/run/env_debug"
    echo "Python executable in ${VENV_NAME}: $(which python3) v$(python3 --version)"
    echo "Anaconda environments info:"
    conda info --envs
    echo "Anaconda packages sources: $(conda config --show-sources)"
    echo "PYTHONPATH: $(env | grep PYTHONPATH)"
    echo "Networking:"
    bash "${APP_ROOT}/run/env_debug"
    env | grep LITELLM_PORT
    echo "Nvidia CUDA properties:"
    nvidia-smi
fi

if [ -z environment.yml ]; then
  conda env export -q --name "${VENV_NAME}" --file environment.yml
fi

# Start API server
if [ -n "${DEV_MODE}" ]; then
    python3 -m debugpy --listen 5678 --wait-for-client -c 'import uvicorn; uvicorn.run("opendevin.server.listen:app", host="0.0.0.0", port='${DEVIN_API_PORT}', reload=True, log_level="debug")'
else
    python3 -c 'import uvicorn; uvicorn.run("opendevin.server.listen:app", host="0.0.0.0", port='${DEVIN_API_PORT}', log_level="critical")'
fi

