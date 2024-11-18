#!/bin/bash

# Print commands and their arguments as they are executed
set -x

{
  # Check that we can use the GPU in PyTorch
  conda run -n agent python -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'WARNING: No GPU')"
  # Check that we can use the GPU in TensorFlow
  conda run -n agent python -c "import tensorflow as tf; print('GPUs Available: ', tf.config.list_physical_devices('GPU'))"

  # wait for agent entrypoint to finish with timeout
  timeout=300 # 5 minutes in seconds
  elapsed=0
  interval=5 # Check every 5 seconds
  while [ ! -f "$AGENT_DIR/entrypoint_done" ]; do
    if [ $elapsed -ge $timeout ]; then
      echo "Error: Agent entrypoint did not finish within $timeout seconds."
      exit 1
    fi
    sleep $interval
    elapsed=$((elapsed + interval))
  done
  echo "Agent entrypoint finished!"

  if ! docker info &>/dev/null; then
    echo "Error: Docker is required but is either not running or not installed."
    exit 1
  fi

  source /opt/conda/bin/activate agent

  sudo ./build.sh \
    && conda run -n agent --no-capture-output python setup.py "$@" \
    && conda run -n agent --no-capture-output python start.py "$@"
} 2>&1 | tee $LOGS_DIR/agent.log
