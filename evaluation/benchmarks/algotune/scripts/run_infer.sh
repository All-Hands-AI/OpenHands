#!/usr/bin/env bash
set -eo pipefail

# Generate the tasks
poetry run python evaluation/benchmarks/algotune/adapter/run_adapter.py --output-path evaluation/benchmarks/algotune/tasks

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
OPTIM_TASK=$4
MAX_ITER=$5
NUM_WORKERS=$6

# Set default values
if [ -z "$NUM_WORKERS" ]; then
  NUM_WORKERS=7
  echo "Number of workers not specified, use default $NUM_WORKERS"
fi

if [ -z "$COMMIT_HASH" ]; then
  COMMIT_HASH=0166df6
  echo "Number of workers not specified, use default $COMMIT_HASH"
fi


if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$OPTIM_TASK" ]; then
  echo "Optimization task not specified, use default kmeans"
  OPTIM_TASK="all"
fi

if [ -z "$MAX_ITER" ]; then
  echo "MAX_ITER not specified, use default 500"
  MAX_ITER=500
fi

checkout_eval_branch
get_openhands_version

echo "AGENT: $AGENT"
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"
echo "OPTIM_TASK: $OPTIM_TASK"
echo "MAX_ITER: $MAX_ITER"
echo "NUM_WORKERS: $NUM_WORKERS"

EVAL_NOTE=$OPENHANDS_VERSION

# Handle enable volumes option
if [ -z "$ENABLE_VOLUMES" ]; then
  export ENABLE_VOLUMES=false
fi
echo "ENABLE_VOLUMES: $ENABLE_VOLUMES"

# Construct the command
COMMAND="poetry run python evaluation/benchmarks/algotune/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --optim_task $OPTIM_TASK \
  --max-iterations $MAX_ITER \
  --eval-num-workers $NUM_WORKERS \
  --enable_volumes $ENABLE_VOLUMES \
  --eval-note $EVAL_NOTE"

# Add custom eval note if provided
if [ -n "$EVAL_NOTE_CUSTOM" ]; then
  echo "EVAL_NOTE_CUSTOM: $EVAL_NOTE_CUSTOM"
  COMMAND="$COMMAND --eval-note $EVAL_NOTE_CUSTOM"
fi

echo "Running command: $COMMAND"

# Run the command
eval $COMMAND
