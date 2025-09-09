#!/usr/bin/env bash

# SWE-Interact evaluation with remote runtime in stateful mode using Tom agent
# This script runs the interactive SWE-bench evaluation using remote runtime with stateful user modeling
# Usage: ./run_interact_remote_tom_stateful.sh [model_name]
# Example: ./run_interact_remote_tom_stateful.sh llm.claude-sonnet-4-20250514

MODEL=${1:-"llm.claude-sonnet-4-20250514"}

CLI_AVAILABLE="false" \
USE_HINT_TEXT="false" \
TOM_AGENT_MODEL="litellm_proxy/claude-sonnet-4-20250514" \
SYSTEM_PROMPT_FILENAME="system_prompt_tom_benchmark.j2" \
ALLHANDS_API_KEY="ah-69ce5388-6069-4c76-9d8d-eae75dd553dc" \
RUNTIME=remote \
SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev" \
EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" \
nohup bash ./evaluation/benchmarks/swe_bench/scripts/run_infer_interact.sh \
  $MODEL \
  HEAD \
  TomCodeActAgent \
  64 \
  100 \
  64 \
  cmu-lti/stateful \
  test \
  1 \
  stateful > swe_bench_interact_remote_tom_stateful_${MODEL//llm./}.log 2>&1 &

echo "SWE-Interact stateful evaluation started with remote runtime and Tom agent using model: $MODEL"
echo "Monitor progress with: tail -f swe_bench_interact_remote_tom_stateful_${MODEL//llm./}.log"
echo "Check if running with: ps aux | grep run_infer_interact"
