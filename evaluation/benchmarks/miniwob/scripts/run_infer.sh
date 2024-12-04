#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

# configure browsing agent
export USE_NAV="false"
export USE_CONCISE_ANSWER="true"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
NOTE=$4
EVAL_LIMIT=$5
NUM_WORKERS=$6

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default BrowsingAgent"
  AGENT="BrowsingAgent"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

EVAL_NOTE="${OPENHANDS_VERSION}_${NOTE}"

COMMAND="export PYTHONPATH=evaluation/benchmarks/miniwob:\$PYTHONPATH && poetry run python evaluation/benchmarks/miniwob/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --eval-num-workers $NUM_WORKERS"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
