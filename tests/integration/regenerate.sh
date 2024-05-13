#!/bin/bash
set -eo pipefail

if [ -z $WORKSPACE_MOUNT_PATH ]; then
  WORKSPACE_MOUNT_PATH=$(pwd)
fi
if [ -z $WORKSPACE_BASE ]; then
  WORKSPACE_BASE=$(pwd)
fi

WORKSPACE_MOUNT_PATH+="/_test_workspace"
WORKSPACE_BASE+="/_test_workspace"

SANDBOX_TYPE="ssh"
MAX_ITERATIONS=10

agents=("MonologueAgent" "CodeActAgent" "PlannerAgent" "SWEAgent")
remind_iterations_config=(false true false false)
tasks=(
  "Fix typos in bad.txt."
  "Write a shell script 'hello.sh' that prints 'hello'."
  "Use Jupyter IPython to write a text file containing 'hello world' to '/workspace/test.txt'."
)
test_names=(
  "test_edits"
  "test_write_simple_script"
  "test_ipython"
)

num_of_tests=${#test_names[@]}
num_of_agents=${#agents[@]}

rm -rf logs
rm -rf $WORKSPACE_BASE
for ((i = 0; i < num_of_tests; i++)); do
  task=${tasks[i]}
  test_name=${test_names[i]}
  for ((j = 0; j < num_of_agents; j++)); do
    agent=${agents[j]}
    remind_iterations=${remind_iterations_config[j]}

    echo -e "\n\n\n\n========Running $test_name for $agent========\n\n\n\n"
    rm -rf $WORKSPACE_BASE
    mkdir $WORKSPACE_BASE
    if [ -d "tests/integration/workspace/$test_name" ]; then
      cp -r tests/integration/workspace/$test_name/* $WORKSPACE_BASE
    fi

    if [ "$TEST_ONLY" = true ]; then
      set -e
    else
      # Temporarily disable 'exit on error'
      set +e
    fi

    SANDBOX_TYPE=$SANDBOX_TYPE \
      WORKSPACE_BASE=$WORKSPACE_BASE \
      REMIND_ITERATIONS=$remind_iterations \
      MAX_ITERATIONS=$MAX_ITERATIONS \
      WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH \
      AGENT=$agent \
      poetry run pytest -s ./tests/integration/test_agent.py::$test_name
    TEST_STATUS=$?
    # Re-enable 'exit on error'
    set -e

    if [[ $TEST_STATUS -ne 0 ]]; then
      echo -e "\n\n\n\n========$test_name failed, regenerating test data for $agent========\n\n\n\n"
      sleep 1

      rm -rf $WORKSPACE_BASE
      mkdir -p $WORKSPACE_BASE
      if [ -d "tests/integration/workspace/$test_name" ]; then
        cp -r tests/integration/workspace/$test_name/* $WORKSPACE_BASE
      fi

      rm -rf logs
      rm -rf tests/integration/mock/$agent/$test_name/*
      # set -x to print the command being executed
      set -x
      echo -e "/exit\n" | \
        SANDBOX_TYPE=$SANDBOX_TYPE \
        WORKSPACE_BASE=$WORKSPACE_BASE \
        DEBUG=true \
        REMIND_ITERATIONS=$remind_iterations \
        WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH \
        AGENT=$agent \
        poetry run python ./opendevin/core/main.py \
        -i $MAX_ITERATIONS \
        -t "$task Do not ask me for confirmation at any point." \
        -c $agent
      set +x

      mkdir -p tests/integration/mock/$agent/$test_name/
      mv logs/llm/**/* tests/integration/mock/$agent/$test_name/
    else
      echo -e "\n\n\n\n========$test_name for $agent PASSED========\n\n\n\n"
      sleep 1
    fi
  done
done

rm -rf logs
rm -rf $WORKSPACE_BASE
echo "Done!"
