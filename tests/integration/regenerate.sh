#!/bin/bash
set -eo pipefail
umask 022

WORKSPACE_MOUNT_PATH=$(pwd)/_test_workspace
WORKSPACE_BASE=$(pwd)/_test_workspace
SANDBOX_TYPE="ssh"

# FIXME: SWEAgent hangs, so it goes last
agents=("MonologueAgent" "CodeActAgent" "PlannerAgent" "SWEAgent")

# TODO: currently we only have one test: test_write_simple_script. We need to revisit
# this script when we have more than one integration test.
for agent in "${agents[@]}"; do
  echo -e "\n\n\n\n========Running integration test for $agent========\n\n\n\n"
  rm -rf $WORKSPACE_BASE

  # Temporarily disable 'exit on error'
  set +e
  SANDBOX_TYPE=$SANDBOX_TYPE WORKSPACE_BASE=$WORKSPACE_BASE \
    WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH AGENT=$agent \
    poetry run pytest ./tests/integration
  TEST_STATUS=$?
  # Re-enable 'exit on error'
  set -e

  if [[ $TEST_STATUS -ne 0 ]]; then
    echo -e "\n\n\n\n========Test failed, regenerating test data for $agent========\n\n\n\n"
    sleep 1
    rm -rf logs
    rm -rf $WORKSPACE_BASE
    rm -rf tests/integration/mock/$agent/test_write_simple_script/*
    mkdir $WORKSPACE_BASE
    echo -e "/exit\n" | SANDBOX_TYPE=$SANDBOX_TYPE WORKSPACE_BASE=$WORKSPACE_BASE \
      WORKSPACE_MOUNT_PATH=$WORKSPACE_MOUNT_PATH AGENT=$agent \
      poetry run python ./opendevin/core/main.py \
      -i 10 \
      -t "Write a shell script 'hello.sh' that prints 'hello'. Do not ask me for confirmation at any point." \
      -c $agent

    mv logs/llm/**/* tests/integration/mock/$agent/test_write_simple_script/
  else
    echo -e "\n\n\n\n========Integration test for $agent PASSED========\n\n\n\n"
    sleep 1
  fi
done

rm -rf logs
rm -rf _test_workspace
echo "Done!"
