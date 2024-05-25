#!/bin/bash

SUBSET=$1
EVAL_LIMIT=$2
AGENT=$3

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_NAME: $MODEL_NAME"

export PYTHONPATH=$(pwd)

COMMAND="poetry run python ./evaluation/mint/run_infer.py \
    --subset $SUBSET \
    --max-iterations 5 \
    --max_propose_solution 2 \
    --eval-n-limit $EVAL_LIMIT \
    --eval-note $AGENT_VERSION"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
