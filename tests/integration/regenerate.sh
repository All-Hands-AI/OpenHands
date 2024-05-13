#!/bin/bash
set -eo pipefail

WORKSPACE_MOUNT_PATH=$(pwd)/_test_workspace
WORKSPACE_BASE=$(pwd)/_test_workspace
SANDBOX_TYPE="ssh"
MAX_ITERATIONS=10

# FIXME: SWEAgent hangs, so it goes last
agents=("MonologueAgent" "CodeActAgent" "PlannerAgent" "SWEAgent")
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

num_of_tests=${#tasks[@]}
num_of_agents=${#agents[@]}

rm -rf logs
rm -rf _test_workspace
for ((i = 0; i < num_of_tests; i++)); do
  task=${tasks[i]}
  test_name=${test_names[i]}
  for ((j = 0; j < num_of_agents; j++)); do
    agent=${agents[j]}

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

    SANDBOX_TYPE=$SANDBOX_TYPE WORKSPACE_BASE=$WORKSPACE_BASE \
      MAX_ITERATIONS=$MAX_ITERATIONS \
      WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH AGENT=$agent \
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
        DEBUG=true REMIND_ITERATIONS=$remind_iterations \
        WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH AGENT=$agent \
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
rm -rf _test_workspace
echo "Done!"
