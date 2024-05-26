#!/bin/bash

set -e

source ~/.bashrc
# ADD /opendevin/plugins to PATH to make `jupyter_cli` available
echo 'export PATH=$PATH:/opendevin/plugins/jupyter' >> ~/.bashrc
export PATH=/opendevin/plugins/jupyter:$PATH

# get current PythonInterpreter
OPENDEVIN_PYTHON_INTERPRETER=$(which python3)

# if user name is `opendevin`, add '/home/opendevin/.local/bin' to PATH
if [ "$USER" = "opendevin" ]; then
    echo 'export PATH=$PATH:/home/opendevin/.local/bin' >> ~/.bashrc
    echo "export OPENDEVIN_PYTHON_INTERPRETER=$OPENDEVIN_PYTHON_INTERPRETER" >> ~/.bashrc
    export PATH=$PATH:/home/opendevin/.local/bin
    export PIP_CACHE_DIR=$HOME/.cache/pip
fi
# if user name is `root`, add '/root/.local/bin' to PATH
if [ "$USER" = "root" ]; then
    echo 'export PATH=$PATH:/root/.local/bin' >> ~/.bashrc
    echo "export OPENDEVIN_PYTHON_INTERPRETER=$OPENDEVIN_PYTHON_INTERPRETER" >> ~/.bashrc
    export PATH=$PATH:/root/.local/bin
    export PIP_CACHE_DIR=$HOME/.cache/pip

fi

# Install dependencies
pip install jupyterlab notebook jupyter_kernel_gateway

# Create logs directory
sudo mkdir -p /opendevin/logs && sudo chmod 777 /opendevin/logs

# Run background process to start jupyter kernel gateway
# write a bash function that finds a free port
find_free_port() {
  local start_port="${1:-20000}"
  local end_port="${2:-65535}"

  for port in $(seq $start_port $end_port); do
    if ! ss -tuln | awk '{print $5}' | grep -q ":$port$"; then
      echo $port
      return
    fi
  done

  echo "No free ports found in the range $start_port to $end_port" >&2
  return 1
}

export JUPYTER_GATEWAY_PORT=$(find_free_port 20000 30000)
jupyter kernelgateway --KernelGatewayApp.ip=0.0.0.0 --KernelGatewayApp.port=$JUPYTER_GATEWAY_PORT > /opendevin/logs/jupyter_kernel_gateway.log 2>&1 &
export JUPYTER_GATEWAY_PID=$!
echo "export JUPYTER_GATEWAY_PID=$JUPYTER_GATEWAY_PID" >> ~/.bashrc
export JUPYTER_GATEWAY_KERNEL_ID="default"
echo "export JUPYTER_GATEWAY_KERNEL_ID=$JUPYTER_GATEWAY_KERNEL_ID" >> ~/.bashrc
echo "JupyterKernelGateway started with PID: $JUPYTER_GATEWAY_PID"

# Start the jupyter_server
export JUPYTER_EXEC_SERVER_PORT=$(find_free_port 30000 40000)
echo "export JUPYTER_EXEC_SERVER_PORT=$JUPYTER_EXEC_SERVER_PORT" >> ~/.bashrc
/opendevin/plugins/jupyter/execute_server > /opendevin/logs/jupyter_execute_server.log 2>&1 &
export JUPYTER_EXEC_SERVER_PID=$!
echo "export JUPYTER_EXEC_SERVER_PID=$JUPYTER_EXEC_SERVER_PID" >> ~/.bashrc
echo "Execution server started with PID: $JUPYTER_EXEC_SERVER_PID"

# Wait until /opendevin/logs/jupyter_kernel_gateway.log contains "is available"
while ! grep -q "at" /opendevin/logs/jupyter_kernel_gateway.log; do
    echo "Waiting for Jupyter kernel gateway to be available..."
    sleep 1
done
# Wait until /opendevin/logs/jupyter_execute_server.log contains "Jupyter kernel created for conversation"
while ! grep -q "kernel created" /opendevin/logs/jupyter_execute_server.log; do
    echo "Waiting for Jupyter kernel to be created..."
    sleep 1
done
echo "Jupyter kernel ready."
