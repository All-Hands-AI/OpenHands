#!/bin/bash
set -eo pipefail

WORKSPACE_MOUNT_PATH=$(pwd)/workspace

# FIXME: SWEAgent hangs, so it goes last
agents=("MonologueAgent" "CodeActAgent" "PlannerAgent" "SWEAgent")

for agent in "${agents[@]}"; do
  echo -e "\n\n\n\n========Generating test data for $agent========\n\n\n\n"
  rm -rf logs
  rm -rf _test_workspace
  mkdir -p tests/integration/mock/$agent/test_write_simple_script/
  rm -rf tests/integration/mock/$agent/test_write_simple_script/*
  mkdir _test_workspace
  echo -e "/exit\n" | poetry run python ./opendevin/core/main.py \
    -i 10 \
    -t "Write a shell script 'hello.sh' that prints 'hello'. Do not ask me for confirmation at any point." \
    -c $agent \
    -d "./_test_workspace"

  mv logs/llm/**/* tests/integration/mock/$agent/test_write_simple_script/
done

rm -rf logs
rm -rf _test_workspace
echo "Done!"
