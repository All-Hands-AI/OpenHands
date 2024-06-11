#!/bin/bash

# configure miniwob website, change URL to yours
export MINIWOB_URL="file:///home/fangzhex/miniwob-plusplus/miniwob/html/miniwob/"

# configure browsing agent
export USE_NAV="false"
export USE_CONCISE_ANSWER="true"


MODEL_CONFIG=$1
AGENT=$2
NOTE=$3
EVAL_LIMIT=$4

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default BrowsingAgent"
  AGENT="BrowsingAgent"
fi

# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

EVAL_NOTE="${AGENT_VERSION}_${NOTE}"

COMMAND="poetry run python evaluation/miniwob/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --max-chars 10000000 \
  --eval-note $EVAL_NOTE"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
