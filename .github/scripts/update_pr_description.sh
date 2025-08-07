#!/bin/bash

set -euxo pipefail
# This script updates the PR description with commands to run the PR locally
# It adds both Docker and uvx commands

# Get the branch name for the PR
BRANCH_NAME=$(gh pr view $PR_NUMBER --json headRefName --jq .headRefName)

# Define the Docker command
DOCKER_RUN_COMMAND="docker run -it --rm \
  -p 3000:3000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --add-host host.docker.internal:host-gateway \
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:$SHORT_SHA-nikolaik \
  --name openhands-app-$SHORT_SHA \
  docker.all-hands.dev/all-hands-ai/openhands:$SHORT_SHA"

# Define the uvx command
UVX_RUN_COMMAND="uvx --python 3.12 --from git+https://github.com/All-Hands-AI/OpenHands@$BRANCH_NAME openhands"

# Get the current PR body
PR_BODY=$(gh pr view $PR_NUMBER --json body --jq .body)

# Prepare the new PR body with both commands
if echo "$PR_BODY" | grep -q "To run this PR locally, use the following command:"; then
  # For existing PR descriptions, replace the command section
  NEW_PR_BODY=$(echo "$PR_BODY" | sed "s|To run this PR locally, use the following command:.*```|To run this PR locally, use the following command:\n\nGUI with Docker:\n```\n$DOCKER_RUN_COMMAND\n```\n\nCLI with uvx:\n```\n$UVX_RUN_COMMAND\n```|s")
else
  # For new PR descriptions
  NEW_PR_BODY="${PR_BODY}

---

To run this PR locally, use the following command:

GUI with Docker:
\`\`\`
$DOCKER_RUN_COMMAND
\`\`\`

CLI with uvx:
\`\`\`
$UVX_RUN_COMMAND
\`\`\`"
fi

# Update the PR description
echo "Updating PR description with Docker and uvx commands"
gh pr edit $PR_NUMBER --body "$NEW_PR_BODY"
