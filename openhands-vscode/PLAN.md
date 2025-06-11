# VS Code Integration Plan for OpenHands

This document outlines the plan to integrate OpenHands with VS Code, focusing on two primary features:
1.  Easily kick off an OpenHands conversation from inside VS Code.
2.  Grab context from open files and text selections and pass that to OpenHands.

## Part 1: VS Code Extension (`odie/openhands-vscode/`)

This new extension will reside in the `odie` repository at `openhands-vscode/`.

### 1. Project Setup

*   **Directory:** `odie/openhands-vscode/`
*   **`package.json`:**
    *   `name`: `openhands-vscode`
    *   `displayName`: "OpenHands Integration"
    *   `description`: "Integrates OpenHands with VS Code for easy conversation starting and context passing."
    *   `version`: `0.0.1`
    *   `publisher`: `openhands`
    *   `engines`: `{ "vscode": "^1.80.0" }` (or latest stable)
    *   `activationEvents`:
        *   `"onCommand:openhands.startConversation"`
        *   `"onCommand:openhands.startConversationWithFileContext"`
        *   `"onCommand:openhands.startConversationWithSelectionContext"`
    *   `main`: `./out/extension.js`
    *   `contributes`:
        *   `commands`:
            *   `{ "command": "openhands.startConversation", "title": "OpenHands: Start New Conversation", "category": "OpenHands" }`
            *   `{ "command": "openhands.startConversationWithFileContext", "title": "OpenHands: Start Conversation with Active File Content", "category": "OpenHands" }`
            *   `{ "command": "openhands.startConversationWithSelectionContext", "title": "OpenHands: Start Conversation with Selected Text", "category": "OpenHands" }`
        *   `menus`:
            *   `editor/context`:
                *   `{ "when": "editorHasSelection", "command": "openhands.startConversationWithSelectionContext", "group": "navigation@1" }`
                *   `{ "command": "openhands.startConversationWithFileContext", "group": "navigation@2" }`
            *   `commandPalette`:
                *   `{ "command": "openhands.startConversation", "when": "true" }`
                *   `{ "command": "openhands.startConversationWithFileContext", "when": "editorIsOpen" }`
                *   `{ "command": "openhands.startConversationWithSelectionContext", "when": "editorHasSelection" }`
    *   `scripts`: `{ "vscode:prepublish": "npm run compile", "compile": "tsc -p ./", "watch": "tsc -watch -p ./" }`
    *   `devDependencies`: `{ "@types/vscode": "^1.80.0", "typescript": "^5.0.0" }`
*   **`tsconfig.json`:** Standard TypeScript configuration for a VS Code extension (module: "commonjs", target: "es2020", outDir: "out", strict: true, esModuleInterop: true).
*   **`src/extension.ts`:** Main logic for the extension.
*   **`.vscodeignore`:** Standard file to exclude `node_modules`, `src`, `*.tsbuildinfo`, etc.
*   **`README.md`:** Basic usage instructions.
*   **`.gitignore`:** To ignore `node_modules/`, `out/`, `*.vsix`.

### 2. Core Logic in `src/extension.ts`

*   **`activate(context: vscode.ExtensionContext)` function:**
    *   Registers the three commands.
*   **Helper Function: `startOpenHandsInTerminal(options: { task?: string; filePath?: string })`:**
    *   Finds an existing VS Code terminal named "OpenHands" or creates a new one.
    *   Shows the terminal.
    *   If `options.filePath` is provided:
        *   Sends the command `openhands --file "${options.filePath}"\n` to the terminal.
    *   Else if `options.task` is provided:
        *   Sanitizes `options.task` (e.g., escaping quotes, backticks).
        *   Sends the command `openhands --task "${sanitizedTask}"\n` to the terminal.
    *   Else (no specific context):
        *   Sends the command `openhands\n` to the terminal.
*   **Command Handlers:**
    *   **`openhands.startConversation`:**
        *   Calls `startOpenHandsInTerminal({});`
    *   **`openhands.startConversationWithFileContext`:**
        *   Gets the active text editor (`vscode.window.activeTextEditor`).
        *   If no editor, shows an error message and returns.
        *   If `editor.document.isUntitled`:
            *   Gets the document content: `editor.document.getText()`.
            *   Calls `startOpenHandsInTerminal({ task: fileContent });`
        *   Else (document has a file path):
            *   Gets the document's file path: `editor.document.uri.fsPath`.
            *   Calls `startOpenHandsInTerminal({ filePath: documentPath });`
    *   **`openhands.startConversationWithSelectionContext`:**
        *   Gets the active text editor.
        *   If no editor or the selection is empty, shows an error message and returns.
        *   Gets the selected text: `editor.document.getText(editor.selection)`.
        *   Calls `startOpenHandsInTerminal({ task: selectedText });`
*   **`deactivate()` function:**
    *   Can be empty for the initial version.

### 3. User Experience

*   User installs `openhands` CLI (e.g., via PyPI), making it available in PATH.
*   User installs this `openhands-vscode` extension from the VS Code Marketplace or a `.vsix` file.
*   Commands are accessible via Command Palette and editor context menus.
*   OpenHands conversations run within a standard VS Code terminal.

## Part 2: OpenHands CLI Enhancements (`odie/openhands/cli/main.py`)

This involves modifying the existing OpenHands Python CLI to improve the "first start" experience in VS Code.

### 1. Detection and Proactive Extension Installation Prompt

*   **On CLI Startup:**
    1.  **Detect VS Code Environment:** Check if the CLI is running inside a VS Code integrated terminal (e.g., `os.environ.get('TERM_PROGRAM') == 'vscode'`).
    2.  **Check Attempt Flag:** Check for a flag file (e.g., `~/.openhands/.vscode_extension_install_attempted`) to see if this process has been run before. If the flag exists, do nothing further regarding extension installation.
    3.  **Attempt Installation (if in VS Code & not previously attempted):**
        *   Print an informational message to the user (e.g., "INFO: Attempting to install/verify the OpenHands VS Code companion extension...").
        *   Execute the command `code --install-extension openhands.openhands-vscode --force` using `subprocess.run()`.
            *   Capture `stdout`, `stderr`, and the `returncode`.
        *   **Handle `code` command outcome:**
            *   **`FileNotFoundError` (or similar if `code` is not in PATH):**
                *   Print: "INFO: Could not automatically install the OpenHands VS Code extension because the 'code' command was not found in your PATH. For a better experience, please install it manually from the VS Code Marketplace (search for 'OpenHands Integration', Publisher: openhands) or by running: `code --install-extension openhands.openhands-vscode` if you add 'code' to your PATH."
            *   **Non-zero `returncode` from `code` command:**
                *   Print: "INFO: Attempted to install/update the OpenHands VS Code extension, but it might have failed or requires your confirmation within VS Code. (Details: Exit Code: [returncode], Output: [stdout], Error: [stderr]). If it didn't install, please try manually from the Marketplace."
            *   **Zero `returncode` from `code` command:**
                *   Print: "INFO: OpenHands VS Code extension installation/update command sent. Please check VS Code for any confirmation prompts. A VS Code reload might be needed for the extension to become fully active."
        *   **Set Attempt Flag:** Create/update the flag file (`~/.openhands/.vscode_extension_install_attempted`) to prevent repeated attempts.
    4.  Proceed with normal CLI operation.

## Mermaid Diagram of Overall Workflow

```mermaid
graph TD
    subgraph User Interaction Layer
        Palette["Command Palette"] -- Triggers --> Cmd1["VSCode Cmd: openhands.startConversation"]
        Palette -- Triggers --> Cmd2["VSCode Cmd: openhands.startConversationWithFileContext"]
        Palette -- Triggers --> Cmd3["VSCode Cmd: openhands.startConversationWithSelectionContext"]

        EditorContextMenu["Editor Context Menu"] -- Triggers --> Cmd2
        EditorContextMenu -- Triggers --> Cmd3
    end

    subgraph VSCode Extension: odie/openhands-vscode/ (src/extension.ts)
        Cmd1 --> StartHelper1["startOpenHandsInTerminal({})"]
        Cmd2 --> LogicFile{"If active file is untitled?"}
        LogicFile -- Yes --> GetFileContent["Get Untitled File Content"]
        GetFileContent --> StartHelper2a["startOpenHandsInTerminal({ task: fileContent })"]
        LogicFile -- No --> GetFilePath["Get Active File Path"]
        GetFilePath --> StartHelper2b["startOpenHandsInTerminal({ filePath: actualFilePath })"]
        Cmd3 --> GetSelection["Get Selected Text"]
        GetSelection --> StartHelper3["startOpenHandsInTerminal({ task: selectedText })"]

        StartHelper1 -- Sends command --> TerminalExecution
        StartHelper2a -- Sends command --> TerminalExecution
        StartHelper2b -- Sends command --> TerminalExecution
        StartHelper3 -- Sends command --> TerminalExecution
    end

    subgraph VSCode Terminal
        TerminalExecution["Terminal: 'openhands' or 'openhands --task \"...\"' or 'openhands --file \"...\"'"] --> OHCli["OpenHands CLI Process (in odie)"]
    end

    subgraph OpenHands CLI (odie/openhands/cli/main.py)
        OHCli -- On Start --> DetectVSCode{"Running in VSCode Terminal?"}
        DetectVSCode -- No --> ContinueNormalCLI["Continue Normal CLI Operation"]
        DetectVSCode -- Yes --> AttemptedBefore{"Install Attempted Before (check flag file)?"}
        AttemptedBefore -- Yes --> ContinueNormalCLI
        AttemptedBefore -- No --> TryInstall["Print 'Attempting to install extension...'\nRun 'code --install-extension ...'"]
        TryInstall --> InstallResult{"'code' command result?"}
        InstallResult -- "Error ('code' not found)" --> PrintManualFallback1["Print 'Could not run code cmd...'"]
        InstallResult -- "Non-zero exit code" --> PrintManualFallback2["Print 'Install cmd failed/needs confirmation...'"]
        InstallResult -- "Zero exit code" --> PrintSuccessInfo["Print 'Install cmd sent, check VSCode for prompts...'"]
        PrintManualFallback1 --> SetFlag["Set install_attempted flag"]
        PrintManualFallback2 --> SetFlag
        PrintSuccessInfo --> SetFlag
        SetFlag --> ContinueNormalCLI
    end
```

This plan aims for a simple, working initial version with a good user experience for linking the CLI and the VS Code extension.

## Part 3: Testing Strategy

To ensure the reliability and correctness of the integration, the following testing approaches will be adopted:

### 1. VS Code Extension (`odie/openhands-vscode/`) - TypeScript Unit Tests

*   **Framework:** VS Code's recommended testing utilities (often using Mocha or Jest, runnable via `vscode-test`).
*   **Location:** Tests will reside in a `src/test` directory within `openhands-vscode/`.
*   **Features to Test (Unit Tests):**
    *   **Command Registration:**
        *   Verify that all three commands (`openhands.startConversation`, `openhands.startConversationWithFileContext`, `openhands.startConversationWithSelectionContext`) are registered upon extension activation.
    *   **`startOpenHandsInTerminal` Helper Function:**
        *   Mock `vscode.window.createTerminal` and `terminal.sendText`.
        *   Test that it calls `createTerminal` with the correct name ("OpenHands").
        *   Test that it calls `terminal.show()`.
        *   Test that it sends the correct `openhands` command when no options are provided.
        *   Test that it sends the correct `openhands --task "..."` command when `options.task` is provided (including basic sanitization if implemented).
        *   Test that it sends the correct `openhands --file "..."` command when `options.filePath` is provided.
    *   **Command Handler: `openhands.startConversation`:**
        *   Mock `startOpenHandsInTerminal`.
        *   Verify it calls `startOpenHandsInTerminal` with empty options.
    *   **Command Handler: `openhands.startConversationWithFileContext`:**
        *   Mock `vscode.window.activeTextEditor` to simulate different scenarios:
            *   No active editor: Verify error message is shown (mock `vscode.window.showErrorMessage`).
            *   Active editor with an untitled document:
                *   Verify `editor.document.getText()` is called.
                *   Verify `startOpenHandsInTerminal` is called with the correct `task` (document content).
            *   Active editor with a saved document:
                *   Verify `editor.document.uri.fsPath` is used.
                *   Verify `startOpenHandsInTerminal` is called with the correct `filePath`.
    *   **Command Handler: `openhands.startConversationWithSelectionContext`:**
        *   Mock `vscode.window.activeTextEditor` to simulate:
            *   No active editor: Verify error message.
            *   Active editor with no selection: Verify error message.
            *   Active editor with a selection:
                *   Verify `editor.document.getText(editor.selection)` is called.
                *   Verify `startOpenHandsInTerminal` is called with the correct `task` (selected text).
*   **Manual/Integration Testing (Beyond Unit Tests for this PR):**
    *   Manually trigger commands from Command Palette and editor context menus.
    *   Verify a terminal opens with the correct `openhands` command executed.
    *   Verify context (file path, task content) is correctly passed to the CLI.

### 2. OpenHands CLI Enhancements (`odie/openhands/cli/main.py`) - Python Unit Tests

*   **Framework:** `pytest` (as used in the `odie` repository).
*   **Location:** New test file, e.g., `tests/unit/cli/test_vscode_integration.py` or similar.
*   **Features to Test (Unit Tests):**
    *   **VS Code Environment Detection:**
        *   Mock `os.environ.get('TERM_PROGRAM')`.
        *   Test that the detection logic correctly identifies when running inside VS Code and when not.
    *   **Flag File Handling (`~/.openhands/.vscode_extension_install_attempted`):**
        *   Mock `os.path.exists` and file read/write operations (e.g., `pathlib.Path.exists`, `pathlib.Path.touch`).
        *   Test that the CLI checks for the flag file.
        *   Test that the CLI creates the flag file after an attempt.
        *   Test that the CLI skips the installation attempt if the flag file exists.
    *   **`code --install-extension` Execution Logic:**
        *   Mock `subprocess.run`.
        *   Test the scenario where `code` command is not found (`FileNotFoundError`):
            *   Verify `subprocess.run` is called correctly.
            *   Verify the correct fallback message is printed (capture `print` output or use `capsys`).
            *   Verify the attempt flag is set.
        *   Test the scenario where `code` command returns a non-zero exit code:
            *   Simulate `subprocess.run` returning a non-zero code, `stdout`, and `stderr`.
            *   Verify the correct informational/error message is printed.
            *   Verify the attempt flag is set.
        *   Test the scenario where `code` command returns a zero exit code:
            *   Simulate `subprocess.run` returning a zero exit code.
            *   Verify the correct success message is printed.
            *   Verify the attempt flag is set.
    *   **Overall Flow:**
        *   Test that if not in VS Code, no installation attempt is made.
        *   Test that if in VS Code and flag exists, no attempt is made.
        *   Test that if in VS Code and flag doesn't exist, an attempt is made and the flag is set.
*   **Manual/Integration Testing:**
    *   Run `openhands` CLI from within a VS Code integrated terminal.
    *   Observe terminal output for correct informational messages regarding extension installation attempt.
    *   If `code` is in PATH, observe if VS Code prompts for extension installation (if not already installed/handled).
    *   Verify the `~/.openhands/.vscode_extension_install_attempted` flag file is created.
    *   Verify on subsequent runs (with the flag file present), the installation attempt is skipped.

This testing strategy aims to cover the core logic of both the new VS Code extension and the modifications to the OpenHands CLI.
