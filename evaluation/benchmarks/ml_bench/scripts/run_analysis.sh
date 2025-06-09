#!/usr/bin/env bash

RESULT_FILE=$1
MODEL_CONFIG=$2

if [ -z "$RESULT_FILE" ]; then
  echo "RESULT_FILE not specified"
  exit 1
fi


if [ -z "$MODEL_CONFIG" ]; then
  echo "Model config not specified, use default"
  MODEL_CONFIG="eval_gpto"
fi

echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "RESULT_FILE: $RESULT_FILE"

COMMAND="poetry run python evaluation/benchmarks/ml_bench/run_analysis.py \
  --llm-config $MODEL_CONFIG \
  --json_file_path $RESULT_FILE"

# Run the command
eval $COMMAND
