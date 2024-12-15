#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

REPO_SPLIT=$1
MODEL_CONFIG=$2
COMMIT_HASH=$3
AGENT=$4
EVAL_LIMIT=$5
MAX_ITER=$6
NUM_WORKERS=$7
DATASET=$8
SPLIT=$9
N_RUNS=${10}

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
  echo "MAX_ITER not specified, use default 100"
  MAX_ITER=100
fi

if [ -z "$USE_INSTANCE_IMAGE" ]; then
  echo "USE_INSTANCE_IMAGE not specified, use default true"
  USE_INSTANCE_IMAGE=true
fi

if [ -z "$RUN_WITH_BROWSING" ]; then
  echo "RUN_WITH_BROWSING not specified, use default false"
  RUN_WITH_BROWSING=false
fi


if [ -z "$DATASET" ]; then
  echo "DATASET not specified, use default wentingzhao/commit0_combined"
  DATASET="wentingzhao/commit0_combined"
fi

if [ -z "$REPO_SPLIT" ]; then
  echo "REPO_SPLIT not specified, use default lite"
  REPO_SPLIT=0
fi

if [ -z "$SPLIT" ]; then
  echo "HF SPLIT not specified, use default test"
  SPLIT="test"
fi

export USE_INSTANCE_IMAGE=$USE_INSTANCE_IMAGE
echo "USE_INSTANCE_IMAGE: $USE_INSTANCE_IMAGE"
export RUN_WITH_BROWSING=$RUN_WITH_BROWSING
echo "RUN_WITH_BROWSING: $RUN_WITH_BROWSING"

get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"
echo "HF SPLIT: $SPLIT"
echo "REPO SPLIT: $REPO_SPLIT"

# Default to NOT use Hint
if [ -z "$USE_HINT_TEXT" ]; then
  export USE_HINT_TEXT=false
fi
echo "USE_HINT_TEXT: $USE_HINT_TEXT"
EVAL_NOTE="$OPENHANDS_VERSION"
# if not using Hint, add -no-hint to the eval note
if [ "$USE_HINT_TEXT" = false ]; then
  EVAL_NOTE="$EVAL_NOTE-no-hint"
fi

if [ "$RUN_WITH_BROWSING" = true ]; then
  EVAL_NOTE="$EVAL_NOTE-with-browsing"
fi

if [ -n "$EXP_NAME" ]; then
  EVAL_NOTE="$EVAL_NOTE-$EXP_NAME"
fi

function run_eval() {
  local eval_note=$1
  COMMAND="poetry run python evaluation/benchmarks/commit0_bench/run_infer.py \
    --agent-cls $AGENT \
    --llm-config $MODEL_CONFIG \
    --max-iterations $MAX_ITER \
    --eval-num-workers $NUM_WORKERS \
    --eval-note $eval_note \
    --dataset $DATASET \
    --split $SPLIT \
    --repo-split $REPO_SPLIT"

  if [ -n "$EVAL_LIMIT" ]; then
    echo "EVAL_LIMIT: $EVAL_LIMIT"
    COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
  fi

  # Run the command
  eval $COMMAND
}

unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push
if [ -z "$N_RUNS" ]; then
  N_RUNS=1
  echo "N_RUNS not specified, use default $N_RUNS"
fi

for i in $(seq 1 $N_RUNS); do
  current_eval_note="$EVAL_NOTE-run_$i"
  echo "EVAL_NOTE: $current_eval_note"
  run_eval $current_eval_note
done

checkout_original_branch
