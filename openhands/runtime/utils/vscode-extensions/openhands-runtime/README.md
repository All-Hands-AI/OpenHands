# OpenHands VSCode Runtime Extension

## Overview

The OpenHands VSCode Runtime extension is a headless Visual Studio Code extension designed to integrate with the OpenHands platform as a runtime execution environment. Unlike the full OpenHands tab extension, this lightweight version focuses solely on executing agent actions using native VSCode APIs, without any UI components for chat or configuration.

This extension allows the OpenHands backend to delegate actions such as running commands, reading, writing, and editing files directly within the VSCode environment, providing deep integration with the user's workspace.

## Features

- **Command Execution**: Runs commands in a dedicated VSCode terminal.
- **File Operations**: Reads, writes, and edits files using VSCode's file system APIs, with security restrictions to the workspace.
- **Native Integration**: Leverages VSCode's built-in features for a seamless experience, such as opening files in the editor for viewing or showing diffs.

## Installation

1. **Clone the Repository**: Ensure you have the OpenHands repository cloned locally.
2. **Navigate to the Extension Directory**: Change to the directory containing this extension (`openhands/runtime/utils/vscode-extensions/openhands-runtime`).
3. **Install Dependencies**: Run `npm install` to install the required npm packages.
4. **Build the Extension**: Run `npm run compile` to build the TypeScript code into JavaScript.
5. **Package the Extension**: Use `vsce package` to create a `.vsix` file for installation.
6. **Install in VSCode**: In VSCode, go to the Extensions view, click on the "..." menu, select "Install from VSIX...", and choose the generated `.vsix` file.

## Configuration

Configure the connection to the OpenHands backend by setting the server URL in VSCode settings:

- Open the Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`).
- Select "Preferences: Open Settings (JSON)".
- Add or update the following configuration:

```json
"openhands.serverUrl": "http://localhost:3000"
```

## Usage

This extension operates in the background and does not provide a user interface. It connects to the OpenHands backend upon VSCode startup (if configured) and listens for delegated actions. Ensure that the OpenHands backend is running and configured to use the VSCode runtime for your session.

## Development

- **Source Code**: The source code is located in the `src/extension` directory.
- **Building**: Use `npm run compile` to build the extension. For development, `npm run dev` can be used for watch mode.
- **Testing**: Currently, there are no specific tests for this extension. Contributions to add testing are welcome.

## License

This extension is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please submit issues and pull requests via the OpenHands repository.
