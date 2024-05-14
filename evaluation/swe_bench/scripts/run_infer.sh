#!/bin/bash

AGENT=CodeActAgent
AGENT_VERSION=v1.2
MODEL_CONFIG=$1

# You should add $MODEL_CONFIG in your `config.toml`

poetry run python3 evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 50 \
  --max-chars 10000000 \
  --eval-num-workers 8 \
  --eval-note $AGENT_VERSION
