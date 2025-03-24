# OpenHands Goto Terminal Extension

This VS Code extension automatically opens a terminal when the URL contains the query parameter `?goto=terminal`.

## Features

- Automatically detects the `goto=terminal` query parameter in the URL
- Opens a new terminal when the parameter is present
- Provides a command to manually open a terminal: `openhands-goto-terminal.openTerminal`

## Usage

Simply append `?goto=terminal` to your VS Code URL, and a terminal will automatically open when the editor loads.

Example:
```
https://your-vscode-url.example.com?goto=terminal
```

Or with other parameters:
```
https://your-vscode-url.example.com?param1=value1&goto=terminal
```

## Requirements

- VS Code version 1.94.0 or higher