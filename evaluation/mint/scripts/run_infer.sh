#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
SUBSET=$3
EVAL_LIMIT=$4

checkout_eval_branch

# Only 'CodeActAgent' is supported for MINT now
AGENT="CodeActAgent"

get_agent_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"

export PYTHONPATH=$(pwd)

COMMAND="poetry run python ./evaluation/mint/run_infer.py \
    --llm-config $MODEL_CONFIG \
    --max-iterations 5 \
    --max-propose-solution 2 \
    --eval-note $AGENT_VERSION"

if [ -n "$SUBSET" ]; then
  echo "SUBSET: $SUBSET"
  COMMAND="$COMMAND --subset $SUBSET"
# otherwise default to use the math subset
else
  echo "SUBSET: math"
  COMMAND="$COMMAND --subset math"
fi

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND

checkout_original_branch
