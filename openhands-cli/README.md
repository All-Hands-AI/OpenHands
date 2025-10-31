# OpenHands V1 CLI

A **lightweight, modern CLI** to interact with the OpenHands agent (powered by [agent-sdk](https://github.com/OpenHands/agent-sdk)). 

The [OpenHands V0 CLI (legacy)](https://github.com/OpenHands/OpenHands/tree/main/openhands/cli) is being deprecated.

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

## Resuming Conversations

When you exit a conversation, the CLI will display a conversation ID and a hint for resuming:

```
Conversation ID: 2efacdca-3333-4362-adb6-1d119e9882cd
Hint: run ./openhands-cli --resume 2efacdca-3333-4362-adb6-1d119e9882cd to resume this conversation.
```

The CLI automatically detects how it was invoked and provides the appropriate resume command:

- **Built binary**: `./openhands-cli --resume <conversation-id>`
- **Via uv**: `uv run openhands --resume <conversation-id>`
- **Installed globally**: `openhands --resume <conversation-id>`
- **Custom binary name**: `./my-custom-name --resume <conversation-id>`

### Manual Resume Commands

If you need to resume a conversation manually, use one of these patterns:

```bash
# If using the built binary
./openhands-cli --resume <conversation-id>

# If using uv run
uv run openhands --resume <conversation-id>

# If installed globally
openhands --resume <conversation-id>

# If you renamed the binary
./your-custom-name --resume <conversation-id>
```