#!/usr/bin/env bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
MAX_ITER=$5
NUM_WORKERS=$6

get_openhands_version

echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

EVAL_NOTE="$OPENHANDS_VERSION"
if [ -n "$EXP_NAME" ]; then
  EVAL_NOTE="$EVAL_NOTE-$EXP_NAME"
fi
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

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "DATASET: $DATASET"
echo "SPLIT: $SPLIT"
echo "MAX_ITER: $MAX_ITER"
echo "NUM_WORKERS: $NUM_WORKERS"
echo "COMMIT_HASH: $COMMIT_HASH"
echo "MODE: $MODE"
echo "EVAL_CONDENSER: $EVAL_CONDENSER"

function run_eval() {
  local eval_note="${1}"
  COMMAND="poetry run python ./evaluation/benchmarks/lca_ci_build_repair/run_infer.py \
    --agent-cls $AGENT \
    --llm-config $MODEL_CONFIG \
    --max-iterations $MAX_ITER \
    --eval-num-workers $NUM_WORKERS \
    --eval-note $eval_note "




  echo $COMMAND
  # Run the command
  eval $COMMAND
}

#unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push
run_eval $EVAL_NOTE
