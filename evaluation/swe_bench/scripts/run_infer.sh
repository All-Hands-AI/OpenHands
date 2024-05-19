#!/bin/bash

AGENT=CodeActAgent
# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")
MODEL_CONFIG=$1
EVAL_LIMIT=$2

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"

COMMAND="poetry run python evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --max-iterations 50 \
  --max-chars 10000000 \
  --eval-num-workers 8 \
  --eval-note $AGENT_VERSION"

if [ -n "$MODEL_CONFIG" ]; then
  echo "MODEL_CONFIG: $MODEL_CONFIG"
  COMMAND="$COMMAND --llm-config $MODEL_CONFIG"
fi

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
