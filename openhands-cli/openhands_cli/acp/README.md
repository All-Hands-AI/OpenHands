# OpenHands Agent Client Protocol (ACP) Implementation

This module provides Agent Client Protocol (ACP) support for OpenHands, enabling integration with editors like Zed, Vim, and other ACP-capable clients.

## Overview

The ACP implementation uses the [agent-client-protocol](https://github.com/PsiACE/agent-client-protocol-python) Python SDK to provide a clean, standards-compliant interface for editor integration.

## Features

- **Complete ACP baseline methods**:
  - `initialize` - Protocol negotiation and capabilities exchange
  - `authenticate` - Agent authentication (no-op implementation)
  - `session/new` - Create new conversation sessions
  - `session/prompt` - Send prompts to the agent

- **Session management**: Maps ACP sessions to OpenHands conversation IDs
- **Streaming responses**: Real-time updates via `session/update` notifications
- **Tool integration**: Tool calls and results are streamed to the client
- **Error handling**: Comprehensive error handling and reporting
- **MCP support**: Model Context Protocol integration for external tools and data sources

## Usage

### Starting the ACP Server

```bash
# Using the binary (recommended)
./dist/openhands-acp-server --persistence-dir /tmp/acp_data

# Via main CLI
python -m openhands.agent_server --mode acp --persistence-dir /tmp/acp_data

# Direct module execution
python -m openhands.agent_server.acp --persistence-dir /tmp/acp_data
```

### Building the Binary

```bash
# Build the standalone executable
make build-acp-server

# The binary will be created at: ./dist/openhands-acp-server
```

### Editor Integration

The ACP server communicates over stdin/stdout using NDJSON format with JSON-RPC 2.0 messages.

#### Zed Editor Configuration

Add to your Zed `settings.json`:

```json
{
  "agent_servers": {
    "OpenHands": {
      "command": "/path/to/openhands-acp-server",
      "args": [
        "--persistence-dir", "/tmp/openhands_acp"
      ],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Example Protocol Messages

**Initialize:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": 1,
    "clientCapabilities": {
      "fs": {"readTextFile": true, "writeTextFile": true},
      "terminal": true
    }
  },
  "id": 1
}
```

**Create Session:**
```json
{
  "jsonrpc": "2.0",
  "method": "session/new",
  "params": {
    "cwd": "/path/to/project",
    "mcpServers": []
  },
  "id": 2
}
```

**Send Prompt:**
```json
{
  "jsonrpc": "2.0",
  "method": "session/prompt",
  "params": {
    "sessionId": "session-uuid",
    "prompt": "Help me write a Python function"
  },
  "id": 3
}
```

### ⚠️ Important: JSON-RPC 2.0 Format Required

The ACP server **requires proper JSON-RPC 2.0 format**. Raw JSON without the JSON-RPC wrapper will be ignored.

❌ **Incorrect (will be ignored):**
```json
{
  "protocolVersion": 1,
  "clientCapabilities": {
    "fs": {"readTextFile": true, "writeTextFile": true},
    "terminal": true
  }
}
```

✅ **Correct:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": 1,
    "clientCapabilities": {
      "fs": {"readTextFile": true, "writeTextFile": true},
      "terminal": true
    }
  }
}
```

## Model Context Protocol (MCP) Support

The ACP server supports MCP integration, allowing clients to configure external MCP servers that provide additional tools and data sources to the agent.

### MCP Capabilities

The server advertises MCP support in the `initialize` response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": 1,
    "agentCapabilities": {
      "mcpCapabilities": {
        "http": true,
        "sse": true
      }
    }
  }
}
```

### Configuring MCP Servers

MCP servers can be configured when creating a new session using the `mcpServers` parameter:

```json
{
  "jsonrpc": "2.0",
  "method": "session/new",
  "params": {
    "cwd": "/path/to/project",
    "mcpServers": [
      {
        "name": "filesystem",
        "command": "uvx",
        "args": ["mcp-server-filesystem", "/path/to/allowed/directory"],
        "env": [
          {"name": "LOG_LEVEL", "value": "INFO"}
        ]
      },
      {
        "name": "git",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-git"],
        "env": []
      }
    ]
  },
  "id": 2
}
```

### Supported MCP Server Types

Currently, the ACP server supports **command-line MCP servers** (type 3):

- ✅ **Command-line servers**: Executable MCP servers that communicate via stdio
- ⚠️ **HTTP servers**: Not yet supported (will log a warning and be skipped)
- ⚠️ **SSE servers**: Not yet supported (will log a warning and be skipped)

### MCP Server Configuration Format

Command-line MCP servers use this format:

```typescript
{
  name: string;           // Unique identifier for the MCP server
  command: string;        // Executable command (e.g., "uvx", "npx", "python")
  args: string[];         // Command arguments
  env?: Array<{           // Optional environment variables
    name: string;
    value: string;
  }>;
}
```

### Built-in MCP Servers

OpenHands includes several built-in MCP servers by default:

- **fetch**: HTTP client for making web requests
- **repomix**: Repository analysis and code packing tools

Client-provided MCP servers are merged with these defaults, allowing you to extend the agent's capabilities with custom tools and data sources.

### Example: Adding a Custom MCP Server

```json
{
  "jsonrpc": "2.0",
  "method": "session/new",
  "params": {
    "cwd": "/home/user/project",
    "mcpServers": [
      {
        "name": "database",
        "command": "python",
        "args": ["-m", "my_mcp_server.database"],
        "env": [
          {"name": "DB_CONNECTION_STRING", "value": "postgresql://..."},
          {"name": "DB_TIMEOUT", "value": "30"}
        ]
      }
    ]
  },
  "id": 2
}
```

This configuration will make the custom database MCP server available to the agent, allowing it to query databases, execute SQL, and integrate database operations into its workflow.

## Architecture

The ACP implementation acts as an adapter layer:

1. **Transport Layer**: Uses the `agent-client-protocol` SDK for JSON-RPC communication
2. **Session Management**: Maps ACP sessions to OpenHands conversation IDs
3. **Integration Layer**: Connects to existing OpenHands `ConversationService`
4. **Streaming**: Provides real-time updates via ACP notifications

## Dependencies

- `agent-client-protocol>=0.1.0` - Official ACP Python SDK
- Standard OpenHands dependencies (FastAPI, Pydantic, etc.)

## Testing

Run the ACP-specific tests:

```bash
uv run pytest tests/agent_server/acp/ -v
```

Test with the example client:

```bash
python examples/acp_client_example.py
```

## Future Enhancements

- Session persistence (`session/load` method)
- Rich content support (images, audio)
- Authentication mechanisms
- HTTP and SSE MCP server support
- Advanced streaming capabilities