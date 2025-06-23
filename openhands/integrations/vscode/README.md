# OpenHands VS Code Extension

Start OpenHands conversations directly from VS Code with your current file or selected text.

## What it does

- **Start conversation**: Opens OpenHands in a terminal (intelligently reuses existing terminals when possible)
- **Send current file**: Starts OpenHands with your active file
- **Send selection**: Starts OpenHands with selected text
- **Smart terminal management**: Uses VS Code's Shell Integration API to detect idle terminals and reuse them safely

Access commands via Command Palette (Ctrl+Shift+P) or right-click menu.

## Features

### Intelligent Terminal Reuse
- **Smart Detection**: Uses VS Code's Shell Integration API to probe terminal status
- **Safe Reuse**: Only reuses terminals that are confirmed to be idle
- **Graceful Fallback**: Creates new terminals when Shell Integration is unavailable
- **Cross-Shell Support**: Works with bash, zsh, PowerShell, and fish shells

### Virtual Environment Support
- **Auto-Detection**: Automatically finds and activates Python virtual environments
- **Multiple Patterns**: Supports `.venv`, `venv`, and `.virtualenv` directories
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Setup

1. Install OpenHands: `pip install openhands`
2. Run `openhands` from VS Code terminal (extension installs automatically)

## Requirements

- OpenHands CLI in your PATH
- VS Code 1.80.0+
- Compatible shell for optimal terminal reuse (bash, zsh, PowerShell, fish)
