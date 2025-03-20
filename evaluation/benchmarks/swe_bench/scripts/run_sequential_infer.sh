#!/bin/bash

# This script runs the sequential inference for SWE-Bench
# It's based on run_infer.sh but uses run_sequential_infer.py instead

set -e

# Default values
DATASET="princeton-nlp/SWE-bench"
SPLIT="test"
AGENT_CLS="CodeActAgent"
MAX_ITERATIONS=100
EVAL_NOTE=""
EVAL_N_LIMIT=0
EVAL_OUTPUT_DIR=""
MODEL_CONFIG=""
OPENHANDS_VERSION=""
USE_HINT_TEXT="false"
RUN_WITH_BROWSING="false"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dataset)
      DATASET="$2"
      shift 2
      ;;
    --split)
      SPLIT="$2"
      shift 2
      ;;
    --agent_cls)
      AGENT_CLS="$2"
      shift 2
      ;;
    --max_iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --eval_note)
      EVAL_NOTE="$2"
      shift 2
      ;;
    --eval_n_limit)
      EVAL_N_LIMIT="$2"
      shift 2
      ;;
    --eval_output_dir)
      EVAL_OUTPUT_DIR="$2"
      shift 2
      ;;
    --model_config)
      MODEL_CONFIG="$2"
      shift 2
      ;;
    --openhands_version)
      OPENHANDS_VERSION="$2"
      shift 2
      ;;
    --use_hint_text)
      USE_HINT_TEXT="$2"
      shift 2
      ;;
    --run_with_browsing)
      RUN_WITH_BROWSING="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Print configuration
echo "Running sequential inference with the following configuration:"
echo "DATASET: $DATASET"
echo "SPLIT: $SPLIT"
echo "AGENT_CLS: $AGENT_CLS"
echo "MAX_ITERATIONS: $MAX_ITERATIONS"
echo "EVAL_NOTE: $EVAL_NOTE"
echo "EVAL_N_LIMIT: $EVAL_N_LIMIT"
echo "EVAL_OUTPUT_DIR: $EVAL_OUTPUT_DIR"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "USE_HINT_TEXT: $USE_HINT_TEXT"
echo "RUN_WITH_BROWSING: $RUN_WITH_BROWSING"

# Export environment variables
export USE_HINT_TEXT=$USE_HINT_TEXT
export RUN_WITH_BROWSING=$RUN_WITH_BROWSING

# Run the sequential inference
python -m evaluation.benchmarks.swe_bench.run_sequential_infer \
  --dataset "$DATASET" \
  --split "$SPLIT" \
  --agent_cls "$AGENT_CLS" \
  --max_iterations "$MAX_ITERATIONS" \
  --eval_note "$EVAL_NOTE" \
  --eval_n_limit "$EVAL_N_LIMIT" \
  --eval_output_dir "$EVAL_OUTPUT_DIR" \
  --llm_config "$MODEL_CONFIG"