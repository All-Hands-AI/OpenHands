#!/bin/bash

# Simple batch analysis script for agent interactions
# Usage: ./batch_analyze.sh [agent_filter] [model_filter]

ANALYZE_SCRIPT="/home/xuhuizhou/OpenHands/evaluation/benchmarks/swe_bench/analyze_interact.py"
BASE_DIR="/home/xuhuizhou/OpenHands/evaluation/evaluation_outputs/outputs/cmu-lti__interactive-swe-test"

AGENT_FILTER="$1"
MODEL_FILTER="$2"

echo "Searching for evaluation directories..."
echo "Agent filter: ${AGENT_FILTER:-*}"
echo "Model filter: ${MODEL_FILTER:-*}"

for agent_dir in "$BASE_DIR"/*; do
    [[ ! -d "$agent_dir" ]] && continue

    agent=$(basename "$agent_dir")
    [[ -n "$AGENT_FILTER" && "$agent" != *"$AGENT_FILTER"* ]] && continue

    for model_dir in "$agent_dir"/*; do
        [[ ! -d "$model_dir" ]] && continue
        [[ ! -f "$model_dir/output.jsonl" ]] && continue

        model=$(basename "$model_dir")
        [[ -n "$MODEL_FILTER" && "$model" != *"$MODEL_FILTER"* ]] && continue

        echo "Analyzing: $agent/$model"
        python "$ANALYZE_SCRIPT" "$model_dir" -o "$model_dir/interact_analysis.json"
        echo "----------------------------------------"
    done
done
