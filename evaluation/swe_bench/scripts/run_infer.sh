#!/bin/bash

AGENT=CodeActAgent
AGENT_VERSION=v$(python3 -c "from agenthub.codeact_agent import CodeActAgent; print(CodeActAgent.VERSION)")
MODEL_CONFIG=$1

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

# You should add $MODEL_CONFIG in your `config.toml`

poetry run python3 evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 50 \
  --max-chars 10000000 \
  --eval-num-workers 8 \
  --eval-note $AGENT_VERSION
