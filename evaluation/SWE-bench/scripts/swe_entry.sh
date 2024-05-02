#!/bin/bash

set -e

# if user name is `opendevin`, add '/home/opendevin/.local/bin' to PATH
if [ "$USER" = "opendevin" ]; then
    echo 'export PATH=$PATH:/home/opendevin/.local/bin' >> ~/.bashrc
fi
# if user name is `root`, add '/root/.local/bin' to PATH
if [ "$USER" = "root" ]; then
    echo 'export PATH=$PATH:/root/.local/bin' >> ~/.bashrc
    export PATH=$PATH:/root/.local/bin
fi
source ~/.bashrc

SWEUTIL_DIR=/swe_util

# # Install dependencies
# sudo apt-get update && \
#     sudo apt-get install -y libffi-dev python3.11 build-essential && \
#     sudo apt-get clean && \
#     sudo rm -rf /var/lib/apt/lists/*
# sudo ln -sfn /bin/bash /bin/sh

# Create logs directory
sudo mkdir -p /opendevin/logs && sudo chmod 777 /opendevin/logs

# FIXME: Cannot read SWE_INSTANCE_ID from the environment variable
SWE_INSTANCE_ID=django__django-11099

# Read the swe-bench-test-lite.json file and extract the required item based on instance_id
item=$(jq --arg INSTANCE_ID "$SWE_INSTANCE_ID" '.[] | select(.instance_id == $INSTANCE_ID)' $SWEUTIL_DIR/eval_data/instances/swe-bench-test-lite.json)

if [[ -z "$item" ]]; then
  echo "No item found for the provided instance ID."
  exit 1
fi

CONDA_ENV_NAME=$(echo "$item" | jq -r '.repo + "__" + .version | gsub("/"; "__")')

echo "CONDA_ENV_NAME: $CONDA_ENV_NAME"

    # Dump test_patch to /workspace/test.patch
echo "$item" | jq -r '.test_patch' > /workspace/test.patch

    # Dump patch to /workspace/gold.patch
echo "$item" | jq -r '.patch' > /workspace/gold.patch

    # Dump the item to /workspace/instance.json except for the "test_patch" and "patch" fields
echo "$item" | jq 'del(.test_patch, .patch)' > /workspace/instance.json


# Copy repo to workspace
if [ -d /workspace/$CONDA_ENV_NAME ]; then
    rm -rf /workspace/$CONDA_ENV_NAME
fi
cp -r $SWEUTIL_DIR/eval_data/testbeds/$CONDA_ENV_NAME /workspace

# Reset swe-bench testbed and install the repo
source ~/.bashrc
. $SWEUTIL_DIR/miniconda3/etc/profile.d/conda.sh
conda config --set changeps1 False
conda config --append channels conda-forge
conda init bash
conda activate swe-bench-eval

mkdir -p /workspace/reset_testbed_temp
mkdir -p /workspace/reset_testbed_log_dir
output=$(export PYTHONPATH=/OD-SWE-bench && \
    cd /OD-SWE-bench && python swebench/harness/reset_swe_env.py \
    --swe_bench_tasks $SWEUTIL_DIR/eval_data/instances/swe-bench-test.json \
    --temp_dir /workspace/reset_testbed_temp \
    --testbed /workspace \
    --conda_path $SWEUTIL_DIR/miniconda3 \
    --instance_id $SWE_INSTANCE_ID \
    --log_dir /workspace/reset_testbed_log_dir \
    --timeout 900 \
    --verbose)

REPO_PATH=$(echo "$output" | awk -F': ' '/repo_path:/ {print $2}')
echo "Repo Path: $REPO_PATH"

if [[ "$REPO_PATH" == "None" ]]; then
    echo "Error: Failed to retrieve repository path. Tests may not have passed or output was not as expected." >&2
    exit 1
fi

# FIXME: It hangs here.
# Activate instance-specific environment
. $SWEUTIL_DIR/miniconda3/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME