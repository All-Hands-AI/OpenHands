#!/bin/bash
set -eo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CASES_DIR=$SCRIPT_DIR/cases
AGENTHUB_DIR=$SCRIPT_DIR/../../agenthub
# Check if DEBUG variable is already set
if [ -z "${DEBUG}" ]; then
    read -p "Enter value for DEBUG (leave blank for default): " debug_value
    if [ -n "${debug_value}" ]; then
        export DEBUG="${debug_value}"
    else
        export DEBUG="0"
    fi
fi
# Check if OPENAI_API_KEY variable is already set
if [ -z "${OPENAI_API_KEY}" ]; then
    read -sp "Enter value for OPENAI_API_KEY: " openai_key
    echo
    export OPENAI_API_KEY="${openai_key}"
fi
# Get the  MODEL variable
read -sp "Enter value for model running agents: " model
echo

if [ -z "$model" ]; then
    MODEL="gpt-4-0125-preview"
else
    MODEL="$model"
fi

echo "Running with model: $MODEL" 

# add python path
export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR/../../" 

agents=("CodeActAgent" "LangchainsAgent")

# for each agent
for agent in ${agents[@]}; do
  echo "agent: $agent"
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
    agent_dir=$outputs_dir/$agent
    echo "agent output dir: $agent_dir"
    # create agent dir if not exist
    if [ ! -d "$agent_dir" ]; then
       mkdir -p $agent_dir
    fi
    rm -rf $agent_dir/workspace
    if [[ -d $case_dir/start ]]; then
      cp -r $case_dir/start $agent_dir/workspace
    else
      mkdir $agent_dir/workspace
    fi
    echo "running agent: $agent"
    python3 $SCRIPT_DIR/../../opendevin/main.py -d $agent_dir/workspace -c $agent -t "${task}" -m $MODEL -i 10 | tee $agent_dir/logs.txt
    rm -rf $agent_dir/workspace/.git
  done
done
