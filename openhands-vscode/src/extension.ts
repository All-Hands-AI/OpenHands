import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

// Helper function to create a new terminal and send a command
function startOpenHandsInTerminal(options: { task?: string; filePath?: string }): void {
  // Always create a new terminal for starting OpenHands
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  const terminalName = `OpenHands ${timestamp}`;
  const terminal = vscode.window.createTerminal(terminalName);
  terminal.show(true); // true to preserve focus on the editor

  // Try to detect and activate virtual environment first
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  let activationCommand = '';

  if (workspaceFolder) {
    const venvPaths = ['.venv', 'venv', '.virtualenv'];
    for (const venvPath of venvPaths) {
      const venvFullPath = path.join(workspaceFolder.uri.fsPath, venvPath);
      try {
        // Check if virtual environment exists
        if (fs.existsSync(venvFullPath)) {
          // Activate the virtual environment
          const isWindows = process.platform === 'win32';
          const activateScript = isWindows ? 'Scripts\\activate' : 'bin/activate';
          activationCommand = `source "${venvFullPath}/${activateScript}" && `;
          // Show debug info - using error message to force visibility
          vscode.window.showErrorMessage(`DEBUG: Found venv at ${venvFullPath}`);
          break;
        }
      } catch (error) {
        // Virtual environment doesn't exist, continue checking
      }
    }
    if (!activationCommand) {
      vscode.window.showErrorMessage(`DEBUG: No venv found in workspace ${workspaceFolder.uri.fsPath}`);
    }
  } else {
    vscode.window.showErrorMessage('DEBUG: No workspace folder found');
  }

  let commandToSend = `${activationCommand}openhands`;

  if (options.filePath) {
    // Ensure filePath is properly quoted if it contains spaces or special characters
    const safeFilePath = options.filePath.includes(' ') ? `"${options.filePath}"` : options.filePath;
    commandToSend = `${activationCommand}openhands --file ${safeFilePath}`;
  } else if (options.task) {
    // Sanitize task string for command line (basic sanitization)
    // Replace backticks and double quotes that might break the command
    // A more robust sanitization might be needed depending on expected task content
    const sanitizedTask = options.task.replace(/`/g, '\\`').replace(/"/g, '\\"');
    commandToSend = `${activationCommand}openhands --task "${sanitizedTask}"`;
  }

  // Debug: show the actual command being sent
  vscode.window.showErrorMessage(`DEBUG: Sending command: ${commandToSend}`);
  terminal.sendText(commandToSend, true); // true to execute the command (adds newline)
}

export function activate(context: vscode.ExtensionContext) {
  // Command: Start New Conversation
  let startConversationDisposable = vscode.commands.registerCommand('openhands.startConversation', () => {
    startOpenHandsInTerminal({});
  });
  context.subscriptions.push(startConversationDisposable);

  // Command: Start Conversation with Active File Content
  let startWithFileContextDisposable = vscode.commands.registerCommand('openhands.startConversationWithFileContext', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('OpenHands: No active text editor found.');
      return;
    }

    if (editor.document.isUntitled) {
      const fileContent = editor.document.getText();
      if (!fileContent.trim()) {
        vscode.window.showErrorMessage('OpenHands: Active untitled file is empty. Please add content or save the file.');
        return;
      }
      startOpenHandsInTerminal({ task: fileContent });
    } else {
      const documentPath = editor.document.uri.fsPath;
      startOpenHandsInTerminal({ filePath: documentPath });
    }
  });
  context.subscriptions.push(startWithFileContextDisposable);

  // Command: Start Conversation with Selected Text
  let startWithSelectionContextDisposable = vscode.commands.registerCommand('openhands.startConversationWithSelectionContext', () => {
    vscode.window.showErrorMessage('DEBUG: startConversationWithSelectionContext command triggered!');
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('OpenHands: No active text editor found.');
      return;
    }
    if (editor.selection.isEmpty) {
      vscode.window.showErrorMessage('OpenHands: No text selected.');
      return;
    }
    const selectedText = editor.document.getText(editor.selection);
    startOpenHandsInTerminal({ task: selectedText });
  });
  context.subscriptions.push(startWithSelectionContextDisposable);

  // Command: Send Selected Text to Running OpenHands (placeholder for future implementation)
  let sendToRunningOpenHandsDisposable = vscode.commands.registerCommand('openhands.sendSelectionToRunningOpenHands', () => {
    vscode.window.showInformationMessage('OpenHands: Send to running instance feature coming soon!');
    // TODO: Implement sending text to already running OpenHands CLI
    // This would need to:
    // 1. Find the terminal running OpenHands CLI
    // 2. Send the selected text as input to that CLI
    // 3. Handle the case where no OpenHands CLI is running
  });
  context.subscriptions.push(sendToRunningOpenHandsDisposable);
}

export function deactivate() {
  // Clean up resources if needed, though for this simple extension,
  // VS Code handles terminal disposal.
}
