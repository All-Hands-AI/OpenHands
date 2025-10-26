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