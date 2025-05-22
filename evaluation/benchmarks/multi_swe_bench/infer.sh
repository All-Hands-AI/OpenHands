#!/bin/bash


BASE_SCRIPT="./evaluation/benchmarks/multi_swe_bench/scripts/run_infer.sh"

MODELS=("aaa" "bbb" "ccc" "ddd" "fff")
GIT_VERSION="HEAD"
AGENT_NAME="CodeActAgent"
EVAL_LIMIT="500"
MAX_ITER="50"
NUM_WORKERS="1"
LANGUAGE="XXX"
DATASET="XXX"


for MODEL in "${MODELS[@]}"; do
    echo "=============================="
    echo "Running benchmark for MODEL: $MODEL"
    echo "=============================="

    $BASE_SCRIPT \
        "$MODEL" \
        "$GIT_VERSION" \
        "$AGENT_NAME" \
        "$EVAL_LIMIT" \
        "$MAX_ITER" \
        "$NUM_WORKERS" \
        "$DATASET" \
        "$LANGUAGE"

    echo "Completed $MODEL"
done
