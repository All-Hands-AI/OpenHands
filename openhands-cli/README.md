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

## Multi-Platform Builds

The OpenHands CLI supports building native executables for multiple platforms:

- **Linux** (x64) - Built on Ubuntu
- **macOS** (x64) - Built on macOS 
- **Windows** (x64) - Built on Windows with .exe extension

### Automated Builds

GitHub Actions automatically builds binaries for all supported platforms:

- **Pull Requests & Main Branch**: Builds are triggered when CLI files change
- **Releases**: Release binaries are automatically attached to GitHub releases
- **Manual Builds**: Can be triggered via workflow dispatch

### Platform-Specific Notes

- **Linux**: Standard executable, requires glibc
- **macOS**: Universal binary compatible with Intel Macs
- **Windows**: Native .exe executable, no additional dependencies required

All builds use Python 3.12 and include the complete OpenHands agent SDK.