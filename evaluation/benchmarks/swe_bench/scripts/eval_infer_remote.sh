#!/usr/bin/env bash
set -eo pipefail

INPUT_FILE=$1
NUM_WORKERS=$2
DATASET=$3
SPLIT=$4

if [ -z "$INPUT_FILE" ]; then
  echo "INPUT_FILE not specified (should be a path to a jsonl file)"
  exit 1
fi

if [ -z "$DATASET" ]; then
  echo "DATASET not specified, use default princeton-nlp/SWE-bench_Lite"
  DATASET="princeton-nlp/SWE-bench_Lite"
fi

if [ -z "$SPLIT" ]; then
  echo "SPLIT not specified, use default test"
  SPLIT="test"
fi

if [ -z "$NUM_WORKERS" ]; then
  echo "NUM_WORKERS not specified, use default 1"
  NUM_WORKERS=1
fi

echo "... Evaluating on $INPUT_FILE ..."

COMMAND="poetry run python evaluation/benchmarks/swe_bench/eval_infer.py \
  --eval-num-workers $NUM_WORKERS \
  --input-file $INPUT_FILE \
  --dataset $DATASET \
  --split $SPLIT"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND

# update the output with evaluation results
poetry run python evaluation/benchmarks/swe_bench/scripts/eval/update_output_with_eval.py $INPUT_FILE
