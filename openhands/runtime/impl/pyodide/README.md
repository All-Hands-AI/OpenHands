# Pyodide Runtime

The Pyodide Runtime provides a secure and efficient runtime environment for executing actions through Pyodide MCP (Model Context Protocol). It enables bash command execution and file editing capabilities in a controlled environment.

## Configuration

To use the Pyodide runtime, you need to configure it in your `config.toml`:

1. Set the runtime type in the core section:

```toml
[core]
runtime = "pyodide"
```

2. Configure Pyodide MCP settings in the MCP section:

```toml
[mcp]
[mcp.pyodide]
url = "your_pyodide_mcp_url"  # Required: The URL for Pyodide MCP server
```

## Features

The Pyodide Runtime provides:

- **Bash Command Execution**: Execute bash commands in a controlled environment
- **File Editing**: Edit files through the Pyodide MCP interface
- **Event Streaming**: Real-time event handling and status updates
- **Plugin Support**: Extensible through plugin requirements
- **Environment Variables**: Configurable environment variables
- **Headless Mode**: Support for headless operation

## Implementation Details

The runtime implements:

- Connection management with automatic retry (120s timeout)
- Status callback support for monitoring runtime state
- Event stream integration
- A2A (Agent-to-Agent) manager support
- Plugin system integration

## Usage

The Pyodide Runtime is typically initialized and managed through the `AgentSession` class:

```python
from openhands.server.session.agent_session import AgentSession
from openhands.core.config import AppConfig
from openhands.events.stream import EventStream
from openhands.storage.files import FileStore

# Create an agent session
session = AgentSession(
    sid="your_session_id",
    file_store=FileStore(),
    status_callback=your_callback,
    user_id="your_user_id"
)

# Start the session with Pyodide runtime
await session.start(
    runtime_name="pyodide",
    config=AppConfig(),
    agent=your_agent,
    max_iterations=250,
    git_provider_tokens=your_tokens,
    selected_repository=your_repo,
    selected_branch="main"
)

# The session will handle runtime initialization and connection
# including:
# - Creating the runtime instance
# - Connecting to the runtime
# - Setting up plugins
# - Cloning repository if specified
# - Running setup scripts if needed

# Close the session when done
await session.close()
```

## Status Messages

The runtime provides status updates through the status callback:

- `STATUS$WAITING_FOR_CLIENT`: Initial connection state
- ` `: Runtime ready

## Error Handling

The runtime includes:

- Automatic retry for connection issues
- Connection timeout after 120 seconds
- Graceful error handling for missing configurations
