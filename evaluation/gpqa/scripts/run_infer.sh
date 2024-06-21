#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
EVAL_LIMIT=$3
DATA_SPLIT=$4
AGENT=$5

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

get_agent_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

COMMAND="poetry run python evaluation/gpqa/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --max-chars 10000000 \
  --eval-num-workers 1 \
  --data-split $DATA_SPLIT \
  --eval-note $AGENT_VERSION"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
