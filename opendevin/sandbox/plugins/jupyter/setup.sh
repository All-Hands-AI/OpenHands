#!/bin/bash

set -ex

pip install jupyterlab notebook jupyter_kernel_gateway

# ADD /opendevin/plugins to PATH to make `jupyter_cli` available
echo 'export PATH=$PATH:/opendevin/plugins/jupyter' >> ~/.bashrc
export PATH=$PATH:/opendevin/plugins/jupyter

# if user name is `opendevin`, add '/home/opendevin/.local/bin' to PATH
if [ "$USER" = "opendevin" ]; then
    echo 'export PATH=$PATH:/home/opendevin/.local/bin' >> ~/.bashrc
    export PATH=$PATH:/home/opendevin/.local/bin
fi
# if user name is `root`, add '/root/.local/bin' to PATH
if [ "$USER" = "root" ]; then
    echo 'export PATH=$PATH:/root/.local/bin' >> ~/.bashrc
    export PATH=$PATH:/root/.local/bin
fi

# Run background process to start jupyter kernel gateway
export JUPYTER_GATEWAY_PORT=18888
jupyter kernelgateway --KernelGatewayApp.ip=0.0.0.0 --KernelGatewayApp.port=$JUPYTER_GATEWAY_PORT &
export JUPYTER_GATEWAY_PID=$!
export JUPYTER_GATEWAY_KERNEL_ID="default"
echo "JupyterKernelGateway started with PID: $JUPYTER_GATEWAY_PID"

# Start the jupyter_server
/opendevin/plugins/jupyter/execute_server &
export JUPYTER_EXEC_SERVER_PID=$!
echo "Execution server started with PID: $JUPYTER_EXEC_SERVER_PID"
