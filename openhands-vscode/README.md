# OpenHands Integration for VS Code

This extension provides integration with OpenHands, allowing you to easily start conversations and pass context from your VS Code editor.

## Features

*   **Start New Conversation:** Quickly open a new OpenHands session in the VS Code terminal.
    *   Command: `OpenHands: Start New Conversation`
*   **Start Conversation with Active File Content:** Send the entire content of your currently active file to a new OpenHands session.
    *   Command: `OpenHands: Start Conversation with Active File Content`
    *   Accessible via editor context menu (right-click in editor).
*   **Start Conversation with Selected Text:** Send only the currently selected text from your active editor to a new OpenHands session.
    *   Command: `OpenHands: Start Conversation with Selected Text`
    *   Accessible via editor context menu (right-click in editor when text is selected).

## Requirements

*   **OpenHands CLI:** You must have the `openhands` command-line tool installed and available in your system's PATH. Install it via PyPI: `pip install openhands`.
*   **VS Code:** Version 1.80.0 or higher.

## Usage

1.  Install the `openhands` CLI tool.
2.  Start `openhands` from the vscode integrated terminal and accept the prompts.
3.  Use the commands from the Command Palette (Ctrl+Shift+P or Cmd+Shift+P) or by right-clicking in the editor.

## How it Works

The extension launches the `openhands` CLI in a new or existing VS Code terminal named "OpenHands".
- For file context, it uses `openhands --file /path/to/your/file.ext`.
- For untitled files or selected text, it uses `openhands --task "your content..."`.

## CLI Interaction for First-Time Use

When you run the `openhands` CLI for the first time from a VS Code integrated terminal, it may attempt to automatically install this companion extension for a smoother experience. Please follow any prompts in VS Code.

## Development

1.  Clone the repository (this extension is part of the main OpenHands repository, located in `openhands-vscode/`).
2.  Navigate to the `openhands-vscode/` directory.
3.  Run `npm install` to install dependencies.
4.  Open the `openhands-vscode/` directory in VS Code.
5.  Press `F5` to open a new VS Code window with the extension loaded (Extension Development Host).
6.  Make your changes in the original VS Code window. The Extension Development Host will reload as you make changes to the TypeScript files (if `npm run watch` is active or after manual compilation).

To compile:
```bash
npm run compile
```

To watch for changes and compile:
```bash
npm run watch
```

---

Happy coding with OpenHands!
