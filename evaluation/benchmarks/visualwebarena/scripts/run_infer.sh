#!/usr/bin/env bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

# configure browsing agent
export USE_NAV="true"
export USE_CONCISE_ANSWER="true"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
NUM_WORKERS=$5

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default VisualBrowsingAgent"
  AGENT="VisualBrowsingAgent"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

EVAL_NOTE="${OPENHANDS_VERSION}"

COMMAND="poetry run python evaluation/benchmarks/visualwebarena/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 15 \
  --eval-num-workers $NUM_WORKERS \
  --eval-note $EVAL_NOTE"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
