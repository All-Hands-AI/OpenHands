#!/bin/bash

# set -e

# assert user name is `root`
if [ "$USER" != "root" ]; then
    echo "Error: This script is intended to be run by the 'root' user only." >&2
    exit 1
fi

source ~/.bashrc

SWEUTIL_DIR=/swe_util

# Create logs directory
LOG_DIR=/opendevin/logs
mkdir -p $LOG_DIR && chmod 777 $LOG_DIR

# FIXME: Cannot read SWE_INSTANCE_ID from the environment variable
# SWE_INSTANCE_ID=django__django-11099
if [ -z "$SWE_INSTANCE_ID" ]; then
    echo "Error: SWE_INSTANCE_ID is not set." >&2
    exit 1
fi

# Read the swe-bench-test-lite.json file and extract the required item based on instance_id
item=$(jq --arg INSTANCE_ID "$SWE_INSTANCE_ID" '.[] | select(.instance_id == $INSTANCE_ID)' $SWEUTIL_DIR/eval_data/instances/swe-bench-instance.json)

if [[ -z "$item" ]]; then
  echo "No item found for the provided instance ID."
  exit 1
fi

WORKSPACE_NAME=$(echo "$item" | jq -r '.repo + "__" + .version | gsub("/"; "__")')

echo "WORKSPACE_NAME: $WORKSPACE_NAME"

SWE_TASK_DIR=/opendevin/swe_tasks
mkdir -p $SWE_TASK_DIR
# Dump test_patch to /workspace/test.patch
echo "$item" | jq -r '.test_patch' > $SWE_TASK_DIR/test.patch
# Dump patch to /workspace/gold.patch
echo "$item" | jq -r '.patch' > $SWE_TASK_DIR/gold.patch
# Dump the item to /workspace/instance.json except for the "test_patch" and "patch" fields
echo "$item" | jq 'del(.test_patch, .patch)' > $SWE_TASK_DIR/instance.json

# Clear the workspace
rm -rf /workspace/*
# Copy repo to workspace
if [ -d /workspace/$WORKSPACE_NAME ]; then
    rm -rf /workspace/$WORKSPACE_NAME
fi
cp -r /testbed/ /workspace/$WORKSPACE_NAME/

# Reset swe-bench testbed and install the repo
. /opt/miniconda3/etc/profile.d/conda.sh
conda activate testbed

mkdir -p $SWE_TASK_DIR/reset_testbed_temp
mkdir -p $SWE_TASK_DIR/reset_testbed_log_dir

REPO_PATH=/workspace/$WORKSPACE_NAME
echo "Repo Path: $REPO_PATH"
echo "Test Command: $TEST_CMD"
echo "export REPO_PATH=\"$REPO_PATH\"" >> ~/.bashrc
# echo "export TEST_CMD=\"$TEST_CMD\"" >> ~/.bashrc

if [[ "$REPO_PATH" == "None" ]]; then
    echo "Error: Failed to retrieve repository path. Tests may not have passed or output was not as expected." >&2
    exit 1
fi

# Activate instance-specific environment
. /opt/miniconda3/etc/profile.d/conda.sh
conda activate testbed

# set +e
