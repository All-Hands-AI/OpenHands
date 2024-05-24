#!/bin/bash
MODEL_CONFIG=$1
AGENT=$2
EVAL_LIMIT=$3
LEVELS=$4

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$LEVELS" ]; then
  LEVELS="2023_level1"
  echo "Levels not specified, use default $LEVELS"
fi

# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "LEVELS: $LEVELS"

COMMAND="poetry run python ./evaluation/gaia/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 30 \
  --level $LEVELS \
  --data-split validation \
  --max-chars 10000000 \
  --eval-num-workers 1 \
  --eval-note ${AGENT_VERSION}_${LEVELS}"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
