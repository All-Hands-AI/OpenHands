#!/usr/bin/env bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
HUBS=$5
NUM_WORKERS=$6

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

if [ -z "$HUBS" ]; then
  HUBS="hf,torch,tf"
  echo "Hubs not specified, use default $HUBS"
fi

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "HUBS: $HUBS"

COMMAND="poetry run python evaluation/benchmarks/gorilla/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 30 \
  --hubs $HUBS \
  --data-split validation \
  --eval-num-workers $NUM_WORKERS \
  --eval-note ${OPENHANDS_VERSION}_${LEVELS}"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
