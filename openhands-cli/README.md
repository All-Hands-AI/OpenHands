# OpenHands CLI

A lightweight CLI/TUI to interact with the OpenHands agent (powered by agent-sdk). Build and run locally or as a single executable.

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
