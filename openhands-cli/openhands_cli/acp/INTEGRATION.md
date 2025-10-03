# ACP Integration in openhands-cli

This directory contains the Agent Client Protocol (ACP) implementation for OpenHands CLI, enabling integration with code editors like Zed and Vim.

## Overview

This ACP implementation has been migrated from the agent-sdk repository and integrated directly into openhands-cli. It allows users to run OpenHands as an ACP server that editors can connect to.

## Usage

### Running ACP Mode

```bash
openhands-cli --acp
```

### With Custom Persistence Directory

```bash
openhands-cli --acp --persistence-dir ~/.my-custom-path
```

### Editor Configuration (Zed Example)

Add to your Zed `settings.json`:

```json
{
  "agent_servers": {
    "OpenHands": {
      "command": "openhands-cli",
      "args": ["--acp"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Architecture

### Components

- **server.py**: Main ACP agent implementation using the `acp` Python package
- **events.py**: Event subscriber that converts SDK events to ACP notifications
- **utils.py**: Utility functions for MCP configuration conversion
- **__main__.py**: Standalone entry point (can run as `python -m openhands_cli.acp`)

### Dependencies

The ACP implementation depends on:
- `acp` package (agent-client-protocol-python)
- `openhands-sdk` (agent, LLM, tools)
- `openhands-agent-server` (ConversationService)

These are declared in `pyproject.toml`.

## Protocol Support

### Baseline Methods (Implemented)

- ✅ `initialize` - Protocol negotiation and capabilities exchange
- ✅ `authenticate` - Optional LLM configuration
- ✅ `session/new` - Create new conversation sessions
- ✅ `session/prompt` - Send prompts and receive streaming responses

### Optional Methods (Implemented)

- ✅ `session/load` - Load existing sessions
- ✅ `session/set_mode` - Set session mode (e.g., confirmation mode)
- ✅ `session/cancel` - Cancel ongoing operations

### Notifications (Sent)

- ✅ `session/update` - Streaming updates during prompt processing
  - `thinking` - Agent is processing
  - `tool_use` - Tool is being invoked
  - `tool_result` - Tool result received
  - `agent_message_chunk` - Streaming agent response
  - `request_permission` - Requesting user approval

## Features

- **MCP Support**: Configure Model Context Protocol servers
- **Streaming Responses**: Real-time updates via notifications
- **Session Management**: Persistent sessions across prompts
- **Tool Integration**: Full access to OpenHands tools
- **Error Handling**: Comprehensive error reporting

## Testing

Run tests for ACP:

```bash
cd openhands-cli
uv run pytest tests/ -k acp
```

## Development

### Making Changes

1. The ACP implementation is in `openhands_cli/acp/`
2. Tests should go in `tests/test_acp_*.py`
3. Follow the existing code style

### Debugging

Enable debug logging:

```bash
DEBUG=true openhands-cli --acp
```

## Migration Notes

This code was migrated from `agent-sdk/openhands/agent_server/acp/` with minimal changes:
- Import paths remain the same (using openhands.agent_server)
- Dependencies added to openhands-cli's pyproject.toml
- Integration hook added to simple_main.py

## Resources

- [ACP Protocol Specification](https://agentclientprotocol.com/protocol/overview)
- [ACP Python SDK](https://github.com/PsiACE/agent-client-protocol-python)
- [OpenHands SDK Documentation](https://github.com/All-Hands-AI/agent-sdk)

## Support

For issues or questions:
- Check the README.md in this directory
- Review the ACP protocol documentation
- Ask in OpenHands Discord #development channel
