#!/bin/bash

# Files with only formatting changes to check out from main
FILES_TO_CHECKOUT=(
  "openhands/agenthub/codeact_agent/codeact_agent.py"
  "openhands/agenthub/loc_agent/function_calling.py"
  "openhands/agenthub/loc_agent/loc_agent.py"
  "openhands/core/config/app_config.py"
  "openhands/core/config/mcp_config.py"
  "openhands/events/observation/mcp.py"
  "openhands/mcp/utils.py"
  "openhands/runtime/impl/docker/docker_runtime.py"
  "openhands/server/config/server_config.py"
  "openhands/server/conversation_manager/standalone_conversation_manager.py"
  "openhands/server/routes/conversation.py"
  "openhands/server/routes/health.py"
  "openhands/server/routes/manage_conversations.py"
  "openhands/server/routes/mcp.py"
  "openhands/server/services/conversation.py"
  "openhands/server/session/agent_session.py"
  "openhands/server/session/session.py"
  "openhands/storage/conversation/conversation_store.py"
)

echo "Checking out files with only formatting changes from main branch..."

for file in "${FILES_TO_CHECKOUT[@]}"; do
  echo "Checking out $file from main..."
  git checkout main -- "$file"
done

echo "Done!"