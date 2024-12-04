#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
DATASET=$2
COMMIT_HASH=$3
EVAL_LIMIT=$4
AGENT=$5
NUM_WORKERS=$6

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
# ################################################################################

checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$DATASET" ]; then
  echo "Dataset not specified, use default ProofWriter"
  DATASET="ProofWriter"
fi

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

COMMAND="poetry run python evaluation/benchmarks/logic_reasoning/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --dataset $DATASET \
  --max-iterations 10 \
  --eval-num-workers $NUM_WORKERS \
  --eval-note $OPENHANDS_VERSION"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
