# OpenHands VS Code Extension

Start OpenHands conversations directly from VS Code with your current file or selected text.

## What it does

- **Start conversation**: Opens OpenHands in a terminal (safely reuses idle terminals or creates new ones)
- **Send current file**: Starts OpenHands with your active file
- **Send selection**: Starts OpenHands with selected text
- **Safe terminal management**: Never interrupts running processes; creates new terminals when needed

Access commands via Command Palette (Ctrl+Shift+P) or right-click menu.

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

## Setup

1. Install OpenHands: `pip install openhands`
2. Run `openhands` from VS Code terminal (extension installs automatically)

## Requirements

- OpenHands CLI in your PATH
- VS Code 1.98.2+
- Compatible shell for optimal terminal reuse (bash, zsh, PowerShell, fish)

## Development

### Setup
```bash
npm install
```

### Building the Extension

The VS Code extension is automatically built during OpenHands installation. The build process:

1. **Automatic Build**: When installing OpenHands via `pip install`, the extension is built automatically
2. **Pre-built Extension**: A pre-built `.vsix` file is included for systems with older Node.js versions
3. **Node.js Requirements**: Building from source requires Node.js >= 14

#### Build Options

- **Skip Build**: Set `SKIP_VSCODE_BUILD=1` to skip building and use the pre-built extension
- **Force Rebuild**: Delete the `.vsix` file to force a rebuild on next install

#### Manual Build
```bash
# Package the extension manually
npm run package-vsix
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
