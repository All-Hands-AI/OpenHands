#!/usr/bin/env bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
DATASET=$5
HARDNESS=$6
WOLFRAM_APPID=$7
NUM_WORKERS=$8

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$DATASET" ]; then
  DATASET="flight"
  echo "Dataset not specified, use default $DATASET"
fi

if [ -z "$HARDNESS" ]; then
  HARDNESS="easy"
  echo "Hardness not specified, use default $HARDNESS"
fi

if [ -z "$WOLFRAM_APPID" ]; then
  WOLFRAM_APPID="YOUR_WOLFRAMALPHA_APPID"
  echo "WOLFRAM_APPID not specified"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"
echo "HARDNESS: $HARDNESS"
echo "WOLFRAM_APPID: $WOLFRAM_APPID"

COMMAND="poetry run python evaluation/benchmarks/toolqa/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 30 \
  --dataset $DATASET \
  --hardness $HARDNESS \
  --wolfram-alpha-appid $WOLFRAM_APPID\
  --data-split validation \
  --eval-num-workers $NUM_WORKERS \
  --eval-note ${OPENHANDS_VERSION}_${LEVELS}"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
