#!/bin/bash

# Print commands and their arguments as they are executed
set -x

# run the root entrypoint in the background
/entrypoint.sh &

mkdir -p $LOGS_DIR
mkdir -p $AGENT_DIR
{
  # Check if Docker installed, and if so start the Docker daemon in the background.
  if [ -x "$(command -v docker)" ]; then

    # if CUDA is available, install the nvidia container toolkit
    if [ -x "$(command -v nvidia-smi)" ]; then
      # configure production repository
      curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
        | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
          | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
      # install the nvidia container toolkit
      sudo apt-get update
      sudo apt-get install -y nvidia-container-toolkit
      # configure the runtime
      sudo nvidia-ctk runtime configure --runtime=docker
    fi

    # (re)start the Docker daemon
    if sudo pgrep dockerd > /dev/null; then
      sudo pkill dockerd
    fi
    sudo dockerd > $LOGS_DIR/docker.log 2>&1 &
    sleep 5
  else
    echo "Docker not installed. Skipping Docker startup."
  fi

} 2>&1 | tee $LOGS_DIR/agent_entrypoint.log

# signal that the entrypoint has finished
touch $AGENT_DIR/entrypoint_done

# wait for root entrypoint (a server), need this otherwise the container exits
wait
