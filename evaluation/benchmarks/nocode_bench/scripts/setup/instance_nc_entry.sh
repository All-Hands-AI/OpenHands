#!/usr/bin/env bash

source ~/.bashrc
SWEUTIL_DIR=/swe_util

if [ -z "$SWE_INSTANCE_ID" ]; then
    echo "Error: SWE_INSTANCE_ID is not set." >&2
    exit 1
fi


item=$(jq --arg INSTANCE_ID "$SWE_INSTANCE_ID" '.[] | select(.instance_id == $INSTANCE_ID)' $SWEUTIL_DIR/eval_data/instances/swe-bench-instance.json)


if [[ -z "$item" ]]; then
  echo "No item found for the provided instance ID."
  exit 1
fi

REPO_NAME=$(echo "$item" | jq -r '.repo | split("/")[-1]')
WORKSPACE_NAME="$REPO_NAME"


echo "WORKSPACE_NAME: $WORKSPACE_NAME"


# Clear the workspace
if [ -d /workspace ]; then
    rm -rf /workspace/*
else
    mkdir /workspace
fi
# Copy repo to workspace
if [ -d /workspace/$WORKSPACE_NAME ]; then
    rm -rf /workspace/$WORKSPACE_NAME
fi
mkdir -p /workspace

SRC_DIR="/root/$REPO_NAME"
DEST_DIR="/workspace/$WORKSPACE_NAME"

cp -r "$SRC_DIR" "$DEST_DIR"



echo ">> Extracting conda environment name..."
CONDA_ENV_NAME=$(echo "$item" | jq -r '.conda_env // empty')

# Activate instance-specific environment
if [ -d /opt/miniconda3 ]; then
    . /opt/miniconda3/etc/profile.d/conda.sh
    conda activate $CONDA_ENV_NAME
fi


