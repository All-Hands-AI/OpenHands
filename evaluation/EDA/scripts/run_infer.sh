#!/bin/bash
MODEL_CONFIG=$1
AGENT=$2
DATASET=$3
EVAL_LIMIT=$4

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$DATASET" ]; then
  echo "Dataset not specified, use default 'things'"
  DATASET="things"
fi

# check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY is not set, please set it to run the script"
  exit 1
fi

# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"

COMMAND="poetry run python evaluation/EDA/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --dataset $DATASET \
  --data-split test \
  --max-iterations 20 \
  --OPENAI_API_KEY $OPENAI_API_KEY \
  --max-chars 10000000 \
  --eval-num-workers 1 \
  --eval-note ${AGENT_VERSION}_${DATASET}"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
