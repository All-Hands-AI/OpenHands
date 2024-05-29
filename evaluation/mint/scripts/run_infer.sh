#!/bin/bash

MODEL_CONFIG=$1
SUBSET=$2
EVAL_LIMIT=$3
# Only 'CodeActAgent' is supported for MINT now
AGENT="CodeActAgent"

# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"

export PYTHONPATH=$(pwd)

COMMAND="poetry run python ./evaluation/mint/run_infer.py \
    --max-iterations 5 \
    --max-propose-solution 2 \
    --eval-note $AGENT_VERSION"

if [ -n "$SUBSET" ]; then
  echo "SUBSET: $SUBSET"
  COMMAND="$COMMAND --subset $SUBSET"
# otherwise default to use the math subset
else
  echo "SUBSET: math"
  COMMAND="$COMMAND --subset math"
fi

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
