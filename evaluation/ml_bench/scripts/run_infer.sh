#!/bin/bash

MODEL_CONFIG=$1
SPLIT=$2
AGENT=$3
EVAL_LIMIT=$4

if [ -z "$MODEL_CONFIG" ]; then
  echo "Model config not specified, use default"
  MODEL_CONFIG="eval_gpt4_1106_preview"
fi

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

COMMAND="poetry run python evaluation/ml_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --eval-num-workers 4 \
  --eval-note $AGENT_VERSION"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

if [ -n "$SPLIT" ]; then
  echo "SPLIT: $SPLIT"
  COMMAND="$COMMAND --eval-split $SPLIT"
fi

# Run the command
eval $COMMAND
