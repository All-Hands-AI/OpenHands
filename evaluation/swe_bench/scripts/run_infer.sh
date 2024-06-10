#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4
MAX_ITER=$5

checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

if [ -z "$MAX_ITER" ]; then
  echo "MAX_ITER not specified, use default 30"
  MAX_ITER=30
fi

get_agent_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

# Default to use Hint
if [ -z "$USE_HINT_TEXT" ]; then
  export USE_HINT_TEXT=true
fi
echo "USE_HINT_TEXT: $USE_HINT_TEXT"
EVAL_NOTE="$AGENT_VERSION"
# if not using Hint, add -no-hint to the eval note
if [ "$USE_HINT_TEXT" = false ]; then
  EVAL_NOTE="$EVAL_NOTE-no-hint"
fi

unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push

COMMAND="poetry run python evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations $MAX_ITER \
  --max-chars 10000000 \
  --eval-num-workers 8 \
  --eval-note $EVAL_NOTE"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND

checkout_original_branch
