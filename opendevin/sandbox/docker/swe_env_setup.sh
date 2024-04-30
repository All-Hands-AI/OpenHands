#!/bin/bash

set -e

# # ADD /opendevin/plugins to PATH to make `jupyter_cli` available
# echo 'export PATH=$PATH:/opendevin/plugins/jupyter' >> ~/.bashrc
# export PATH=/opendevin/plugins/jupyter:$PATH

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

# Install dependencies
sudo apt-get update && \
    sudo apt-get install -y libffi-dev python3.11 build-essential && \
    sudo apt-get clean && \
    sudo rm -rf /var/lib/apt/lists/*

sudo ln -sfn /bin/bash /bin/sh

# Create logs directory
sudo mkdir -p /opendevin/logs && sudo chmod 777 /opendevin/logs

# Create SWE-bench directories
echo "SWEUTIL_DIR: $SWEUTIL_DIR"
echo "PATH: $PATH"

# Install miniconda3
if [ ! -d $CACHE_DIR/miniconda3 ]; then
    bash $CACHE_DIR/Miniconda3-latest-Linux-x86_64.sh -b -p $CACHE_DIR/miniconda3
fi
echo 'export PATH=$CACHE_DIR/miniconda3/bin:${PATH}' >> ~/.bashrc
source ~/.bashrc
conda --version
conda config --set changeps1 False
conda config --append channels conda-forge
conda init bash

# Clone swe-bench-eval environment
if [ ! -d $CACHE_DIR/miniconda3/envs/swe-bench-eval ]; then
    conda create --clone $SWEUTIL_DIR/conda_envs/swe-bench-eval --name swe-bench-eval
fi

# Read the swe-bench-lite-test.json file and extract the required item based on instance_id
item=$(jq --arg INSTANCE_ID "$SWE_INSTANCE_ID" '.[] | select(.instance_id == $INSTANCE_ID)' $CACHE_DIR/swe-bench-lite-test.json)

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


# Clone instance-specific environment
# CONDA_ENV_NAME=$(jq -r --arg id $SWE_INSTANCE_ID '.[$id].conda_env_name' $CACHE_DIR/swe_config.json)
# echo "Code Env Name: $CONDA_ENV_NAME"
if [ ! -d $CACHE_DIR/miniconda3/envs/$CONDA_ENV_NAME ]; then
    conda create --clone $SWEUTIL_DIR/conda_envs/$CONDA_ENV_NAME --name $CONDA_ENV_NAME
fi

# Copy repo to workspace
if [ -d /workspace/$CONDA_ENV_NAME ]; then
    rm -rf /workspace/$CONDA_ENV_NAME
fi
cp -r $SWEUTIL_DIR/harness_materials/yizhou_testbeds/$CONDA_ENV_NAME /workspace

# Reset swe-bench testbed and install the repo
source ~/.bashrc
conda init
conda activate swe-bench-eval

output=$(cd $SWEUTIL_DIR/OD-SWE-bench/swebench/harness && python reset_swe_env.py \
    --swe_bench_tasks $SWEUTIL_DIR/harness_materials/processed/swe-bench-test.json \
    --temp_dir $SWEUTIL_DIR/harness_materials/eval_temp_swe_env \
    --testbed /workspace \
    --conda_path $CACHE_DIR/miniconda3 \
    --instance_id $SWE_INSTANCE_ID \
    --log_dir $SWEUTIL_DIR/harness_materials/eval_logs_swe_env \
    --timeout 900 \
    --verbose)

REPO_PATH=$(echo "$output" | awk -F': ' '/repo_path:/ {print $2}')
echo "Repo Path: $REPO_PATH"

if [[ "$REPO_PATH" == "None" ]]; then
    echo "Error: Failed to retrieve repository path. Tests may not have passed or output was not as expected." >&2
    exit 1
fi


# Activate instance-specific environment
source ~/.bashrc
conda init
conda activate $CONDA_ENV_NAME
