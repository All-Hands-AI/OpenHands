#!/bin/bash
MODEL_CONFIG=$1
EVAL_LIMIT=$2
DATA_SPLIT=$3
AGENT=$4

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent ..."
  AGENT="CodeActAgent"
fi

# NOTE: if data split is not provided, use the default value 'gpqa_diamond'
if [ -z "$DATA_SPLIT" ]; then
  echo "Data split not specified, using default gpqa_diamond ..."
  DATA_SPLIT="gpqa_diamond"
fi

# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

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
