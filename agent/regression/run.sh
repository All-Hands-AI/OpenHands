#!/bin/bash
set -eo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CASES_DIR=$SCRIPT_DIR/cases

# iterate over cases dir
for case in $(ls $CASES_DIR); do
  # run the case
  if [[ -n $TEST_CASE && $case != $TEST_CASE ]]; then
    continue
  fi
  echo "Running case: $case"
  case_dir=$CASES_DIR/$case
  task=$(cat $case_dir/task.txt)
  docker run -e DEBUG=$DEBUG -e OPENAI_API_KEY=$OPENAI_API_KEY -v $case_dir/workspace:/workspace control-loop python /app/main.py /workspace "${task}" | tee $case_dir/logs.txt
done
