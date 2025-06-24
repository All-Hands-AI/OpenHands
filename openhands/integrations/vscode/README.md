# OpenHands VS Code Extension

A unified VS Code extension that provides both launcher and runtime capabilities for OpenHands:
- **Launcher**: Start OpenHands conversations directly from VS Code with your current file or selected text
- **Runtime**: Execute OpenHands actions directly within VS Code (file operations, editor commands, etc.)

## What it does

### Launcher Features
- **Start conversation**: Opens OpenHands in a terminal (safely reuses idle terminals or creates new ones)
- **Send current file**: Starts OpenHands with your active file
- **Send selection**: Starts OpenHands with selected text
- **Safe terminal management**: Never interrupts running processes; creates new terminals when needed

Access launcher commands via Command Palette (Ctrl+Shift+P) or right-click menu.

### Runtime Features
- **Backend Communication**: Connects to OpenHands backend via WebSocket for real-time action execution
- **File Operations**: Execute file read/write operations directly in VS Code
- **Editor Commands**: Perform editor actions like opening files, navigating to lines, etc.
- **Automatic Connection**: Connects to OpenHands backend when available, gracefully handles offline state

## Features

### Safe Terminal Management
- **Non-Intrusive**: Never interrupts running processes in existing terminals
- **Smart Reuse**: Only reuses terminals that have completed OpenHands commands
- **Safe Fallback**: Creates new terminals when existing ones may be busy
- **Shell Integration**: Uses VS Code's Shell Integration API when available for better command tracking
- **Conservative Approach**: When in doubt, creates a new terminal to avoid conflicts

### Virtual Environment Support
- **Auto-Detection**: Automatically finds and activates Python virtual environments
- **Multiple Patterns**: Supports `.venv`, `venv`, and `.virtualenv` directories
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Runtime Configuration
- **Server URL**: Configure OpenHands backend URL via VS Code settings (`openhands.serverUrl`)
- **Auto-Connect**: Automatically attempts to connect to backend on extension startup
- **Graceful Fallback**: Works offline when backend is not available

## Setup

1. Install OpenHands: `pip install openhands`
2. Install the VS Code extension (extension installs automatically when you run `openhands`)
3. **Optional**: Configure OpenHands backend URL in VS Code settings:
   - Open VS Code Settings (Ctrl+,)
   - Search for "openhands"
   - Set "OpenHands: Server URL" (default: `http://localhost:3000`)

## Requirements

- OpenHands CLI in your PATH
- VS Code 1.98.2+
- Compatible shell for optimal terminal reuse (bash, zsh, PowerShell, fish)

## Development

### Setup
```bash
npm install
```

### Code Quality
```bash
# Run linting with fixes
npm run lint:fix

# Type checking
npm run typecheck

# Compile TypeScript
npm run compile

# Run tests
npm run test
```

The extension uses ESLint and Prettier for code quality, adapted from the main OpenHands frontend configuration.
