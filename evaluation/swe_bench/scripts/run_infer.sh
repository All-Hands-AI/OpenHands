#!/bin/bash

AGENT=CodeActAgent
# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")
MODEL_CONFIG=$1

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

# You should add $MODEL_CONFIG in your `config.toml`

poetry run python evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 50 \
  --max-chars 10000000 \
  --eval-num-workers 8 \
  --eval-note $AGENT_VERSION
