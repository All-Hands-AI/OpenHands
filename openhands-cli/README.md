# OpenHands CLI

A lightweight CLI/TUI to interact with the OpenHands agent (powered by agent-sdk). Build and run locally or as a single executable.

## Features

- 🖥️ **Interactive TUI**: Terminal-based interface for chatting with the agent
- 📝 **ACP Mode**: Agent Client Protocol support for editor integration (Zed, Vim, etc.)
- 🔧 **Flexible**: Run locally with Python or as a standalone executable
- 🚀 **Powered by agent-sdk**: Full access to OpenHands capabilities

## Quickstart

- Prerequisites: Python 3.12+, curl
- Install uv (package manager):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Restart your shell so "uv" is on PATH, or follow the installer hint
  ```

### Run the CLI locally
```bash
# Install dependencies (incl. dev tools)
make install-dev

# Optional: install pre-commit hooks
make install-pre-commit-hooks

# Start the CLI
make run
# or
uv run openhands-cli
```

Tip: Set your model key (one of) so the agent can talk to an LLM:
```bash
export OPENAI_API_KEY=...
# or
export LITELLM_API_KEY=...
```

### Build a standalone executable
```bash
# Build (installs PyInstaller if needed)
./build.sh --install-pyinstaller

# The binary will be in dist/
./dist/openhands-cli            # macOS/Linux
# dist/openhands-cli.exe        # Windows
```

For advanced development (adding deps, updating the spec file, debugging builds), see Development.md.

## ACP Mode (Editor Integration)

OpenHands CLI supports the Agent Client Protocol (ACP), allowing integration with code editors like Zed and Vim.

### Running in ACP Mode

```bash
# Run with default persistence directory (~/.openhands/acp)
openhands-cli --acp

# Run with custom persistence directory
openhands-cli --acp --persistence-dir /path/to/storage
```

### Editor Configuration

#### Zed Editor

Add to your Zed `settings.json` (typically at `~/.config/zed/settings.json`):

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

#### Other Editors

Any editor that supports the Agent Client Protocol can connect to OpenHands. The server:
- Communicates via JSON-RPC 2.0 over stdin/stdout
- Supports all baseline ACP methods (initialize, authenticate, session/new, session/prompt)
- Provides streaming responses via session/update notifications

### Features in ACP Mode

- ✅ Session management across multiple prompts
- ✅ Real-time streaming responses
- ✅ Tool execution with results
- ✅ MCP (Model Context Protocol) server integration
- ✅ Confirmation mode for risky operations

### Troubleshooting ACP Mode

Enable debug logging:
```bash
DEBUG=true openhands-cli --acp
```

For more details, see [openhands_cli/acp/INTEGRATION.md](openhands_cli/acp/INTEGRATION.md).
