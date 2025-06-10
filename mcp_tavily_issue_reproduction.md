# MCP Tavily Issue Reproduction

This document provides instructions for reproducing and analyzing issue #9030: "No matching MCP agent found for tool name: tavily_tavily-search".

## Background

Users have reported that after making many Tavily searches in a conversation, they encounter the following error:

```
Unexpected error while running action: ValueError: No matching MCP agent found for tool name: tavily_tavily-search
```

This issue appears to be related to how connections are managed between the MCP client and the Tavily server. The hypothesis is that either:

1. Connections are not being properly closed, leading to resource exhaustion
2. The Tavily server is rate-limiting or dropping connections after many requests
3. There's a memory leak or other resource issue in the MCP client or server

## Reproduction Scripts

Three scripts have been created to help reproduce and diagnose the issue:

### 1. Basic Reproduction (`reproduce_mcp_tavily_issue.py`)

This script performs multiple consecutive Tavily searches using a single MCP client instance. It's the simplest reproduction case.

```bash
python reproduce_mcp_tavily_issue.py --api-key YOUR_TAVILY_API_KEY --num-searches 50
```

### 2. Connection Management Focus (`reproduce_mcp_connection_issue.py`)

This script creates a new MCP client for each search, simulating how the actual code behaves in the application. It focuses on identifying issues with connection creation and management.

```bash
python reproduce_mcp_connection_issue.py --api-key YOUR_TAVILY_API_KEY --num-searches 50
```

### 3. Resource Monitoring Focus (`reproduce_mcp_connection_pooling.py`)

This script reuses a single MCP client for all searches but adds detailed resource monitoring to track memory usage, file descriptors, and other resources. It helps identify resource leaks.

```bash
python reproduce_mcp_connection_pooling.py --api-key YOUR_TAVILY_API_KEY --num-searches 50
```

## Key Areas to Investigate

When running these scripts, pay attention to:

1. **Connection Management**: In `MCPClient.call_tool()`, a new connection is created for each tool call with `async with self.client:`. If connections are not properly closed, it could lead to resource exhaustion.

2. **Tool Map Population**: The `_initialize_and_list_tools()` method is called during connection setup. If the connection fails or times out, the tool map might not be properly populated.

3. **Tool Lookup**: In `call_tool_mcp()`, it looks for a matching client for the tool name. If the tool map is not properly populated or if the client connection is lost, this lookup would fail.

4. **Resource Leaks**: Watch for increasing memory usage, file descriptor count, or other resources as more searches are performed.

5. **Error Patterns**: Note when errors start occurring and if they follow a pattern (e.g., after a certain number of searches or after a certain amount of time).

## Code Analysis

The key components involved in this issue are:

1. **MCPClient** (`openhands/mcp/client.py`): Manages connections to MCP servers and tool calls.

2. **call_tool_mcp** (`openhands/mcp/utils.py`): Finds the appropriate client for a tool and makes the call.

3. **create_mcp_clients** (`openhands/mcp/utils.py`): Creates and initializes MCP clients.

The most likely issue is in how connections are managed in `MCPClient.call_tool()`:

```python
async def call_tool(self, tool_name: str, args: dict) -> CallToolResult:
    """Call a tool on the MCP server."""
    if tool_name not in self.tool_map:
        raise ValueError(f'Tool {tool_name} not found.')
    # The MCPClientTool is primarily for metadata; use the session to call the actual tool.
    if not self.client:
        raise RuntimeError('Client session is not available.')

    async with self.client:  # <-- This creates a new connection for each call
        return await self.client.call_tool_mcp(name=tool_name, arguments=args)
```

Each call to `call_tool()` creates a new connection with `async with self.client:`. If these connections are not properly closed, it could lead to resource exhaustion.

## Potential Solutions

While this document focuses on reproducing the issue rather than fixing it, potential solutions might include:

1. **Connection Pooling**: Implement a connection pool to reuse connections instead of creating new ones for each call.

2. **Connection Cleanup**: Ensure connections are properly closed after use.

3. **Retry Mechanism**: Add a retry mechanism for failed connections.

4. **Resource Monitoring**: Add monitoring for connection and resource usage to detect and prevent issues.

5. **Connection Timeout**: Reduce the connection timeout to fail faster if a connection cannot be established.
