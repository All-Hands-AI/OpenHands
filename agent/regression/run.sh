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
  rm -rf $case_dir/workspace
  if [[ -d $case_dir/start ]]; then
    cp -r $case_dir/start $case_dir/workspace
  else
    mkdir $case_dir/workspace
  fi
  docker run -e DEBUG=$DEBUG -e OPENAI_API_KEY=$OPENAI_API_KEY -v $case_dir/workspace:/workspace control-loop python /app/main.py /workspace "${task}" | tee $case_dir/logs.txt
  rm -rf $case_dir/workspace/.git
done
