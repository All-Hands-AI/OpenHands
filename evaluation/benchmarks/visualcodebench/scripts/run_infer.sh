#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

# Check if required arguments are provided
if [ "$#" -lt 4 ]; then
    echo "Usage: $0 [model_config] [commit_hash] [agent_cls] [eval_limit] [num_workers]"
    echo "Example: $0 llm.eval_gpt_4o_mini HEAD CodeActAgent 5 1"
    exit 1
fi

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT_CLS=$3
EVAL_LIMIT=$4
NUM_WORKERS=${5:-1}  # Default to 1 worker if not specified

# Checkout the specified commit
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

COMMAND="export PYTHONPATH=evaluation/benchmarks/visualcodebench:\$PYTHONPATH && poetry run python evaluation/benchmarks/visualcodebench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 5 \
  --eval-num-workers $NUM_WORKERS \
  --eval-note $OPENHANDS_VERSION" \

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
