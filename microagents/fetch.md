---
name: fetch
type: knowledge
version: 1.0.0
agent: CodeActAgent
trigger_type: always
mcp_tools:
  stdio_servers:
    - name: "fetch"
      command: "uvx"
      args: ["mcp-server-fetch"]
      env:
        MCP_FETCH_TIMEOUT: "30"
# We leave the body empty because MCP tools will automatically add the 
# tool description for LLMs.
---
