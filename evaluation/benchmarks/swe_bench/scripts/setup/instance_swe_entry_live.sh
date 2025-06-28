#!/usr/bin/env bash

source ~/.bashrc
SWEUTIL_DIR=/swe_util

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


echo "WORKSPACE_NAME: $SWE_INSTANCE_ID"

# Clear the workspace
if [ -d /workspace ]; then
    rm -rf /workspace/*
else
    mkdir /workspace
fi
# Copy repo to workspace
if [ -d /workspace/$SWE_INSTANCE_ID ]; then
    rm -rf /workspace/$SWE_INSTANCE_ID
fi
mkdir -p /workspace
cp -r /testbed /workspace/$SWE_INSTANCE_ID

# SWE-bench-Live does not use conda to manage Python
# if [ -d /opt/miniconda3 ]; then
#     . /opt/miniconda3/etc/profile.d/conda.sh
#     conda activate testbed
# fi
