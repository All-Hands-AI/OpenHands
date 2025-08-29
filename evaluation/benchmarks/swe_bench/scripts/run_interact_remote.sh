#!/usr/bin/env bash

# SWE-Interact evaluation with remote runtime
# This script runs the interactive SWE-bench evaluation using remote runtime with 64 workers
CLI_AVAILABLE="False" \
USE_HINT_TEXT="False" \
ALLHANDS_API_KEY="ah-69ce5388-6069-4c76-9d8d-eae75dd553dc" \
RUNTIME=remote \
SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.eval.all-hands.dev" \
EVAL_DOCKER_IMAGE_PREFIX="us-central1-docker.pkg.dev/evaluation-092424/swe-bench-images" \
nohup bash ./evaluation/benchmarks/swe_bench/scripts/run_infer_interact.sh \
  llm.claude-sonnet-4-20250514 \
  HEAD \
  CodeActAgent \
  500 \
  100 \
  32 \
  test > swe_bench_interact_remote_32_claude_sonnet_4_20250514.log 2>&1 &

echo "SWE-Interact evaluation started with remote runtime and 32 workers"
echo "Monitor progress with: tail -f swe_bench_interact_remote_32_claude_sonnet_4_20250514.log"
echo "Check if running with: ps aux | grep run_infer_interact"
