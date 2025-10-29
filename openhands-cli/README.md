# OpenHands V1 CLI

A **lightweight, modern CLI** to interact with the OpenHands agent (powered by [agent-sdk](https://github.com/All-Hands-AI/agent-sdk)). 

The [OpenHands V0 CLI (legacy)](https://github.com/All-Hands-AI/OpenHands/tree/main/openhands/cli) is being deprecated.

---

## Quickstart

- Prerequisites: Python 3.12+, curl
- Install uv (package manager):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Restart your shell so "uv" is on PATH, or follow the installer hint
  ```

### Run the CLI locally
```bash
make install

# Start the CLI
make run
# or
uv run openhands
```

### Build a standalone executable
```bash
# Build (installs PyInstaller if needed)
./build.sh --install-pyinstaller

# The binary will be in dist/
./dist/openhands            # macOS/Linux
# dist/openhands.exe        # Windows
```

## Enterprise Gateway Support

For enterprise users with custom LLM gateways, you can provide a gateway configuration file to handle authentication and custom headers/parameters.

### Using Gateway Configuration

```bash
# Using command line flag
uv run openhands --gateway-config ~/mycompany-gateway.toml

# Or using environment variable
export OPENHANDS_GATEWAY_CONFIG=~/mycompany-gateway.toml
uv run openhands
```

See `examples/gateway-config-example.toml` for a complete configuration example with comments.

### Key Features

- **OAuth2/Token Exchange**: Automatically handles token acquisition and refresh
- **Custom Headers**: Add headers required by your gateway
- **Environment Variables**: Use `${ENV:VAR_NAME}` syntax for sensitive values
- **Extra Body Parameters**: Include additional fields in LLM request bodies
- **TOML Format**: Clean, readable configuration with comments