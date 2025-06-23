import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Probes a terminal to check if it's idle using Shell Integration API
 * @param terminal The terminal to probe
 * @returns Promise<boolean> true if terminal is idle, false if busy or probe failed
 */
async function probeTerminalStatus(terminal: vscode.Terminal): Promise<boolean> {
  if (!terminal.shellIntegration) {
    return false;
  }

  try {
    const probeId = Date.now();
    const probeCommand = `echo "OPENHANDS_PROBE_${probeId}"`;

    const execution = terminal.shellIntegration.executeCommand(probeCommand);

    // Set up timeout for probe
    const timeout = new Promise<boolean>((_, reject) =>
      setTimeout(() => reject(new Error('Probe timeout')), 2000)
    );

    // Read output to verify response
    const readOutput = async (): Promise<boolean> => {
      try {
        const stream = execution.read();
        let output = '';

        for await (const data of stream) {
          output += data;
          if (output.includes(`OPENHANDS_PROBE_${probeId}`)) {
            // The terminal is responsive
            return true;
          }
        }
        return false;
      } catch (error) {
        return false;
      }
    };

    return await Promise.race([readOutput(), timeout]);
  } catch (error) {
    // Probe failed, assume terminal is busy
    return false;
  }
}

/**
 * Creates a new OpenHands terminal with timestamp
 * @returns vscode.Terminal
 */
function createNewOpenHandsTerminal(): vscode.Terminal {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  const terminalName = `OpenHands ${timestamp}`;
  return vscode.window.createTerminal(terminalName);
}

/**
 * Finds an existing OpenHands terminal or creates a new one using intelligent detection
 * @returns Promise<vscode.Terminal>
 */
async function findOrCreateOpenHandsTerminal(): Promise<vscode.Terminal> {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );

  if (openHandsTerminals.length > 0) {
    // Use the most recent terminal
    const terminal = openHandsTerminals[openHandsTerminals.length - 1];

    if (terminal.shellIntegration) {
      // Try intelligent probing with Shell Integration
      const isIdle = await probeTerminalStatus(terminal);
      if (isIdle) {
        return terminal; // Safe to reuse
      }
      // If busy, Shell Integration will safely interrupt when we execute new command
      return terminal;
    }

    // Fallback: create new terminal to avoid conflicts when Shell Integration unavailable
    return createNewOpenHandsTerminal();
  }

  // No existing terminals, create new one
  return createNewOpenHandsTerminal();
}

/**
 * Executes an OpenHands command using Shell Integration when available
 * @param terminal The terminal to execute the command in
 * @param command The command to execute
 */
async function executeOpenHandsCommand(terminal: vscode.Terminal, command: string): Promise<void> {
  if (terminal.shellIntegration) {
    // Use Shell Integration for better control
    const execution = terminal.shellIntegration.executeCommand(command);

    // Monitor execution completion
    const disposable = vscode.window.onDidEndTerminalShellExecution(event => {
      if (event.execution === execution) {
        if (event.exitCode === 0) {
          console.log('OpenHands command completed successfully');
        } else if (event.exitCode !== undefined) {
          console.log(`OpenHands command exited with code ${event.exitCode}`);
        }
        disposable.dispose(); // Clean up the event listener
      }
    });
  } else {
    // Fallback to traditional sendText
    terminal.sendText(command, true);
  }
}

/**
 * Detects and builds virtual environment activation command
 * @returns string The activation command prefix (empty if no venv found)
 */
function detectVirtualEnvironment(): string {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    vscode.window.showErrorMessage('DEBUG: No workspace folder found');
    return '';
  }

  const venvPaths = ['.venv', 'venv', '.virtualenv'];
  for (const venvPath of venvPaths) {
    const venvFullPath = path.join(workspaceFolder.uri.fsPath, venvPath);
    try {
      if (fs.existsSync(venvFullPath)) {
        const isWindows = process.platform === 'win32';
        const activateScript = isWindows ? 'Scripts\\activate' : 'bin/activate';
        const activationCommand = `source "${venvFullPath}/${activateScript}" && `;
        vscode.window.showErrorMessage(`DEBUG: Found venv at ${venvFullPath}`);
        return activationCommand;
      }
    } catch (error) {
      // Virtual environment doesn't exist, continue checking
    }
  }

  vscode.window.showErrorMessage(`DEBUG: No venv found in workspace ${workspaceFolder.uri.fsPath}`);
  return '';
}

/**
 * Builds the OpenHands command with proper sanitization
 * @param options Command options
 * @param activationCommand Virtual environment activation prefix
 * @returns string The complete command to execute
 */
function buildOpenHandsCommand(
  options: { task?: string; filePath?: string },
  activationCommand: string
): string {
  let commandToSend = `${activationCommand}openhands`;

  if (options.filePath) {
    // Ensure filePath is properly quoted if it contains spaces or special characters
    const safeFilePath = options.filePath.includes(' ') ? `"${options.filePath}"` : options.filePath;
    commandToSend = `${activationCommand}openhands --file ${safeFilePath}`;
  } else if (options.task) {
    // Sanitize task string for command line (basic sanitization)
    // Replace backticks and double quotes that might break the command
    const sanitizedTask = options.task.replace(/`/g, '\\`').replace(/"/g, '\\"');
    commandToSend = `${activationCommand}openhands --task "${sanitizedTask}"`;
  }

  return commandToSend;
}

/**
 * Main function to start OpenHands in terminal with intelligent terminal reuse
 * @param options Command options
 */
async function startOpenHandsInTerminal(options: { task?: string; filePath?: string }): Promise<void> {
  try {
    // Find or create terminal using intelligent detection
    const terminal = await findOrCreateOpenHandsTerminal();
    terminal.show(true); // true to preserve focus on the editor

    // Detect virtual environment
    const activationCommand = detectVirtualEnvironment();

    // Build command
    const commandToSend = buildOpenHandsCommand(options, activationCommand);

    // Debug: show the actual command being sent
    vscode.window.showErrorMessage(`DEBUG: Sending command: ${commandToSend}`);

    // Execute command using Shell Integration when available
    await executeOpenHandsCommand(terminal, commandToSend);
  } catch (error) {
    vscode.window.showErrorMessage(`Error starting OpenHands: ${error}`);
  }
}

export function activate(context: vscode.ExtensionContext) {
  // Command: Start New Conversation
  let startConversationDisposable = vscode.commands.registerCommand('openhands.startConversation', async () => {
    await startOpenHandsInTerminal({});
  });
  context.subscriptions.push(startConversationDisposable);

  // Command: Start Conversation with Active File Content
  let startWithFileContextDisposable = vscode.commands.registerCommand('openhands.startConversationWithFileContext', async () => {
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
      await startOpenHandsInTerminal({ task: fileContent });
    } else {
      const filePath = editor.document.uri.fsPath;
      await startOpenHandsInTerminal({ filePath: filePath });
    }
  });
  context.subscriptions.push(startWithFileContextDisposable);

  // Command: Start Conversation with Selected Text
  let startWithSelectionContextDisposable = vscode.commands.registerCommand('openhands.startConversationWithSelectionContext', async () => {
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
    await startOpenHandsInTerminal({ task: selectedText });
  });
  context.subscriptions.push(startWithSelectionContextDisposable);


}

export function deactivate() {
  // Clean up resources if needed, though for this simple extension,
  // VS Code handles terminal disposal.
}
