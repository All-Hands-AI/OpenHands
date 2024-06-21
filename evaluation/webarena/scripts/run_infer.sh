#!/bin/bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

# configure webarena websites and environment
source evaluation/webarena/scripts/webarena_env.sh

# configure browsing agent
export USE_NAV="false"
export USE_CONCISE_ANSWER="true"

MODEL_CONFIG=$1
COMMIT_HASH=$2
AGENT=$3
EVAL_LIMIT=$4

checkout_eval_branch

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default BrowsingAgent"
  AGENT="BrowsingAgent"
fi

get_agent_version

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

EVAL_NOTE="$AGENT_VERSION"

COMMAND="poetry run python evaluation/webarena/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 15 \
  --max-chars 10000000 \
  --eval-note $EVAL_NOTE"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
