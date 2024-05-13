#!/bin/bash

python3 evaluation/swe_bench/run_infer.py \
  --agent-cls CodeActAgent \
  --llm-config eval_deepseek_chat \
  --max-iterations 50 \
  --max-chars 10000000 \
  --eval-num-workers 1 \
  --eval-note v1.1
