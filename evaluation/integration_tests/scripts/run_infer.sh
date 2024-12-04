#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
NUM_WORKERS=$5
EVAL_IDS=$6

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

EVAL_NOTE=$OPENHANDS_VERSION

# Default to NOT use unit tests.
if [ -z "$USE_UNIT_TESTS" ]; then
  export USE_UNIT_TESTS=false
fi
echo "USE_UNIT_TESTS: $USE_UNIT_TESTS"
# If use unit tests, set EVAL_NOTE to the commit hash
if [ "$USE_UNIT_TESTS" = true ]; then
  EVAL_NOTE=$EVAL_NOTE-w-test
fi

# export PYTHONPATH=evaluation/integration_tests:\$PYTHONPATH
COMMAND="poetry run python evaluation/integration_tests/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --eval-num-workers $NUM_WORKERS \
  --eval-note $EVAL_NOTE"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

if [ -n "$EVAL_IDS" ]; then
  echo "EVAL_IDS: $EVAL_IDS"
  COMMAND="$COMMAND --eval-ids $EVAL_IDS"
fi

# Run the command
eval $COMMAND
