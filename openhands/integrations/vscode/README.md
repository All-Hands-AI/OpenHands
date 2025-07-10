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
- **On-Demand Connection**: Connects to backend only when OpenHands is configured to use VSCode as runtime
- **Graceful Fallback**: Works offline when backend is not available

## Setup

1. Install OpenHands: `pip install openhands`
2. Install the VS Code extension (extension installs automatically when you run `openhands`)
3. **Optional**: Configure OpenHands backend URL in VS Code settings:
   - Open VS Code Settings (Ctrl+,)
   - Search for "openhands"
   - Set "OpenHands: Server URL" (default: `http://localhost:3000`)
- **Use Your Current File**: Automatically send the content of your active file to OpenHands to start a task.
- **Use a Selection**: Send only the highlighted text from your editor to OpenHands for focused tasks.
- **Safe Terminal Management**: The extension intelligently reuses idle terminals or creates new ones, ensuring it never interrupts an active process.
- **Automatic Virtual Environment Detection**: Finds and uses your project's Python virtual environment (`.venv`, `venv`, etc.) automatically.

## How to Use

You can access the extension's commands in two ways:

1.  **Command Palette**:
    - Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
    - Type `OpenHands` to see the available commands.
    - Select the command you want to run.

2.  **Editor Context Menu**:
    - Right-click anywhere in your text editor.
    - The OpenHands commands will appear in the context menu.

## Installation

For the best experience, the OpenHands CLI will attempt to install the extension for you automatically the first time you run it inside VSCode.

If you need to install it manually:
1.  Download the latest `.vsix` file from the [GitHub Releases page](https://github.com/All-Hands-AI/OpenHands/releases).
2.  In VSCode, open the Command Palette (`Ctrl+Shift+P`).
3.  Run the **"Extensions: Install from VSIX..."** command.
4.  Select the `.vsix` file you downloaded.

## Requirements

- **OpenHands CLI**: You must have `openhands` installed and available in your system's PATH.
- **VS Code**: Version 1.98.2 or newer.
- **Shell**: For the best terminal reuse experience, a shell with [Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration) is recommended (e.g., modern versions of bash, zsh, PowerShell, or fish).

## Contributing

We welcome contributions! If you're interested in developing the extension, please see the `DEVELOPMENT.md` file in our source repository for instructions on how to get started.
