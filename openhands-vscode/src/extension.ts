import * as vscode from 'vscode';

// Helper function to find or create a terminal and send a command
function startOpenHandsInTerminal(options: { task?: string; filePath?: string }): void {
  const terminalName = 'OpenHands';
  let terminal = vscode.window.terminals.find((t: vscode.Terminal) => t.name === terminalName);

  if (!terminal) {
    terminal = vscode.window.createTerminal(terminalName);
  }
  terminal.show(true); // true to preserve focus on the editor

  let commandToSend = 'openhands';

  if (options.filePath) {
    // Ensure filePath is properly quoted if it contains spaces or special characters
    const safeFilePath = options.filePath.includes(' ') ? `"${options.filePath}"` : options.filePath;
    commandToSend = `openhands --file ${safeFilePath}`;
  } else if (options.task) {
    // Sanitize task string for command line (basic sanitization)
    // Replace backticks and double quotes that might break the command
    // A more robust sanitization might be needed depending on expected task content
    const sanitizedTask = options.task.replace(/`/g, '\\`').replace(/"/g, '\\"');
    commandToSend = `openhands --task "${sanitizedTask}"`;
  }

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
}

export function deactivate() {
  // Clean up resources if needed, though for this simple extension,
  // VS Code handles terminal disposal.
}
