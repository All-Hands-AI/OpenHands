#!/bin/bash
set -eo pipefail

run_test() {
  SANDBOX_TYPE=$SANDBOX_TYPE \
    WORKSPACE_BASE=$WORKSPACE_BASE \
    REMIND_ITERATIONS=$remind_iterations \
    MAX_ITERATIONS=$MAX_ITERATIONS \
    WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH \
    AGENT=$agent \
    poetry run pytest -s ./tests/integration/test_agent.py::$test_name
    # return exit code of pytest
    return $?
}

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

if [ "$num_of_agents" -ne "${#remind_iterations_config[@]}" ]; then
  echo "Every agent must have its own remind_iterations_config"
  exit 1
fi

if [ "$num_of_tests" -ne "${#test_names[@]}" ]; then
  echo "Every task must correspond to one test case"
  exit 1
fi

rm -rf logs
rm -rf $WORKSPACE_BASE
for ((i = 0; i < num_of_tests; i++)); do
  task=${tasks[i]}
  test_name=${test_names[i]}

  # skip other tests if only one test is specified
  if [[ -n "$ONLY_TEST_NAME" && "$ONLY_TEST_NAME" != "$test_name" ]]; then
    continue
  fi

  for ((j = 0; j < num_of_agents; j++)); do
    agent=${agents[j]}

    # skip other agents if only one agent is specified
    if [[ -n "$ONLY_TEST_AGENT" && "$ONLY_TEST_AGENT" != "$agent" ]]; then
      continue
    fi

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

    run_test
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
        WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH AGENT=$agent \
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

      echo -e "\n\n\n\n========$test_name test data regenerated for $agent, rerun test again to verify========\n\n\n\n"
      # Temporarily disable 'exit on error'
      set +e
      run_test
      TEST_STATUS=$?
      # Re-enable 'exit on error'
      set -e

      if [[ $TEST_STATUS -ne 0 ]]; then
        echo -e "\n\n\n\n========$test_name for $agent RERUN FAILED========\n\n\n\n"
        echo -e "There are multiple possibilities:"
        echo -e "  1. The agent is unable to finish the task within $MAX_ITERATIONS steps."
        echo -e "  2. The agent thinks itself has finished the task, but fails the validation in the test code."
        echo -e "  3. There is something non-deterministic in the prompt."
        echo -e "  4. There is a bug in this script, or in OpenDevin code."
        echo -e "NOTE: Some of the above problems could sometimes be fixed by a retry (with a more powerful LLM)."
        echo -e "      You could also consider improving the agent, increasing MAX_ITERATIONS, or skipping this test for this agent."
        exit 1
      else
        echo -e "\n\n\n\n========$test_name for $agent RERUN PASSED========\n\n\n\n"
        sleep 1
      fi


    else
      echo -e "\n\n\n\n========$test_name for $agent PASSED========\n\n\n\n"
      sleep 1
    fi
  done
done

rm -rf logs
rm -rf $WORKSPACE_BASE
echo "Done!"
