#!/usr/bin/env bash
set -eo pipefail

source "evaluation/utils/version_control.sh"

PROCESS_FILEPATH=$1
if [ -z "$PROCESS_FILEPATH" ]; then
    echo "Error: PROCESS_FILEPATH is empty. Usage: ./eval_infer.sh <output_file> [instance_id] [dataset_name] [split]"
    exit 1
fi

get_openhands_version

PROCESS_FILEPATH=$(realpath $PROCESS_FILEPATH)
echo "OPENHANDS_VERSION: $OPENHANDS_VERSION"
echo "PROCESS_FILEPATH: $PROCESS_FILEPATH"

EVAL_NOTE="$OPENHANDS_VERSION"
if [ -n "$EXP_NAME" ]; then
  EVAL_NOTE="$EVAL_NOTE-$EXP_NAME"
fi

function run_eval() {
  COMMAND="poetry run python ./evaluation/benchmarks/lca_ci_build_repair/eval_infer.py \
    --predictions-path $PROCESS_FILEPATH "

  echo "RUNNING: $COMMAND"
  # Run the command
  eval $COMMAND
}

unset SANDBOX_ENV_GITHUB_TOKEN # prevent the agent from using the github token to push
run_eval
