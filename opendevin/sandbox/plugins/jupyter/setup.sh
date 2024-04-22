#!/bin/bash

set -e

# ADD /opendevin/plugins to PATH to make `jupyter_cli` available
echo 'export PATH=$PATH:/opendevin/plugins/jupyter' >> ~/.bashrc
export PATH=/opendevin/plugins/jupyter:$PATH

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

# Install dependencies
pip install jupyterlab notebook jupyter_kernel_gateway

# Create logs directory
sudo mkdir -p /opendevin/logs && sudo chmod 777 /opendevin/logs

# Run background process to start jupyter kernel gateway
export JUPYTER_GATEWAY_PORT=18888
jupyter kernelgateway --KernelGatewayApp.ip=0.0.0.0 --KernelGatewayApp.port=$JUPYTER_GATEWAY_PORT > /opendevin/logs/jupyter_kernel_gateway.log 2>&1 &
export JUPYTER_GATEWAY_PID=$!
echo "export JUPYTER_GATEWAY_PID=$JUPYTER_GATEWAY_PID" >> ~/.bashrc
export JUPYTER_GATEWAY_KERNEL_ID="default"
echo "export JUPYTER_GATEWAY_KERNEL_ID=$JUPYTER_GATEWAY_KERNEL_ID" >> ~/.bashrc
echo "JupyterKernelGateway started with PID: $JUPYTER_GATEWAY_PID"

# Start the jupyter_server
export JUPYTER_EXEC_SERVER_PORT=18889
echo "export JUPYTER_EXEC_SERVER_PORT=$JUPYTER_EXEC_SERVER_PORT" >> ~/.bashrc
/opendevin/plugins/jupyter/execute_server > /opendevin/logs/jupyter_execute_server.log 2>&1 &
export JUPYTER_EXEC_SERVER_PID=$!
echo "export JUPYTER_EXEC_SERVER_PID=$JUPYTER_EXEC_SERVER_PID" >> ~/.bashrc
echo "Execution server started with PID: $JUPYTER_EXEC_SERVER_PID"

# Wait until /opendevin/logs/jupyter_kernel_gateway.log contains "is available"
while ! grep -q "is available" /opendevin/logs/jupyter_kernel_gateway.log; do
    sleep 1
done
# Wait until /opendevin/logs/jupyter_execute_server.log contains "Jupyter kernel created for conversation"
while ! grep -q "Jupyter kernel created for conversation" /opendevin/logs/jupyter_execute_server.log; do
    sleep 1
done
echo "Jupyter kernel ready."
