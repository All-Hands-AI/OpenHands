#!/bin/bash
set -eo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CASES_DIR=$SCRIPT_DIR/cases

docker build -t control-loop $SCRIPT_DIR/..

# iterate over cases dir
for case in $(ls $CASES_DIR); do
  # run the case
  if [[ -n $TEST_CASE && $case != $TEST_CASE ]]; then
    continue
  fi
  echo "Running case: $case"
  case_dir=$CASES_DIR/$case
  task=$(cat $case_dir/task.txt)
  outputs_dir=$case_dir/outputs
  for agent in $(ls $outputs_dir); do
    agent_dir=$outputs_dir/$agent
    echo "agent: $agent_dir"
    rm -rf $agent_dir/workspace
    if [[ -d $case_dir/start ]]; then
      cp -r $case_dir/start $agent_dir/workspace
    else
      mkdir $agent_dir/workspace
    fi
    docker run -e DEBUG=$DEBUG -e OPENAI_API_KEY=$OPENAI_API_KEY -v $agent_dir/workspace:/workspace control-loop python /app/main.py -d /workspace -t "${task}" | tee $agent_dir/logs.txt
    rm -rf $agent_dir/workspace/.git
  done
done
