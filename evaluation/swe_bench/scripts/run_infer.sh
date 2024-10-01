#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
MAX_ITER=$5
NUM_WORKERS=$6
DATASET=$7
SPLIT=$8

if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=1
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi
checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$MAX_ITER" ]; then
  echo "MAX_ITER not specified, use default 30"
  MAX_ITER=30
fi

if [ -z "$USE_INSTANCE_IMAGE" ]; then
  echo "USE_INSTANCE_IMAGE not specified, use default true"
  USE_INSTANCE_IMAGE=true
fi


if [ -z "$DATASET" ]; then
  echo "DATASET not specified, use default princeton-nlp/SWE-bench_Lite"
  DATASET="princeton-nlp/SWE-bench_Lite"
fi

if [ -z "$SPLIT" ]; then
  echo "SPLIT not specified, use default test"
  SPLIT="test"
fi

export USE_INSTANCE_IMAGE=$USE_INSTANCE_IMAGE
echo "USE_INSTANCE_IMAGE: $USE_INSTANCE_IMAGE"

get_agent_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"
echo "SPLIT: $SPLIT"

# Default to NOT use Hint
if [ -z "$USE_HINT_TEXT" ]; then
  export USE_HINT_TEXT=false
fi
echo "USE_HINT_TEXT: $USE_HINT_TEXT"
EVAL_NOTE="$AGENT_VERSION"
# if not using Hint, add -no-hint to the eval note
if [ "$USE_HINT_TEXT" = false ]; then
  EVAL_NOTE="$EVAL_NOTE-no-hint"
fi

if [ -n "$EXP_NAME" ]; then
  EVAL_NOTE="$EVAL_NOTE-$EXP_NAME"
fi
echo "EVAL_NOTE: $EVAL_NOTE"

unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push

COMMAND="poetry run python evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations $MAX_ITER \
  --max-chars 10000000 \
  --eval-num-workers $NUM_WORKERS \
  --eval-note $EVAL_NOTE \
  --dataset $DATASET \
  --split $SPLIT"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND

checkout_original_branch
