#!/usr/bin/env bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
EVAL_LIMIT=$3
DATA_SPLIT=$4
AGENT=$5
NUM_WORKERS=$6

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent ..."
  AGENT="CodeActAgent"
fi

# NOTE: if data split is not provided, use the default value 'gpqa_diamond'
if [ -z "$DATA_SPLIT" ]; then
  echo "Data split not specified, using default gpqa_diamond ..."
  DATA_SPLIT="gpqa_diamond"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

COMMAND="poetry run python evaluation/benchmarks/gpqa/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --eval-num-workers $NUM_WORKERS \
  --data-split $DATA_SPLIT \
  --eval-note $OPENHANDS_VERSION"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
