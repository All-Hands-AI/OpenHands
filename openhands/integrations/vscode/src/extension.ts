import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { SocketService } from "./services/socket-service";
import { VSCodeRuntimeActionHandler } from "./services/runtime-action-handler";

// Create output channel for debug logging
const outputChannel = vscode.window.createOutputChannel("OpenHands Debug");

// Runtime services - initialized in activate()
let socketService: SocketService | null = null;
let runtimeActionHandler: VSCodeRuntimeActionHandler | null = null;

/**
 * This implementation uses VSCode's Shell Integration API.
 *
 * VSCode API References:
 * - Terminal Shell Integration: https://code.visualstudio.com/docs/terminal/shell-integration
 * - VSCode Extension API: https://code.visualstudio.com/api/references/vscode-api
 * - Terminal API Reference: https://code.visualstudio.com/api/references/vscode-api#Terminal
 * - VSCode Source Examples: https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.d.ts
 *
 * Shell Integration Requirements:
 * - Compatible shells: bash, zsh, PowerShell Core, or fish shell
 * - Graceful fallback needed for Command Prompt and other shells
 */

// Track terminals that we know are idle (just finished our commands)
const idleTerminals = new Set<string>();

/**
 * Marks a terminal as idle after our command completes
 * @param terminalName The name of the terminal
 */
function markTerminalAsIdle(terminalName: string): void {
  idleTerminals.add(terminalName);
}

/**
 * Marks a terminal as busy when we start a command
 * @param terminalName The name of the terminal
 */
function markTerminalAsBusy(terminalName: string): void {
  idleTerminals.delete(terminalName);
}

/**
 * Checks if we know a terminal is idle (safe to reuse)
 * @param terminal The terminal to check
 * @returns boolean true if we know it's idle, false otherwise
 */
function isKnownIdleTerminal(terminal: vscode.Terminal): boolean {
  return idleTerminals.has(terminal.name);
}

/**
 * Creates a new OpenHands terminal with timestamp
 * @returns vscode.Terminal
 */
function createNewOpenHandsTerminal(): vscode.Terminal {
  const timestamp = new Date().toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
  });
  const terminalName = `OpenHands ${timestamp}`;
  return vscode.window.createTerminal(terminalName);
}

/**
 * Finds an existing OpenHands terminal or creates a new one using safe detection
 * @returns vscode.Terminal
 */
function findOrCreateOpenHandsTerminal(): vscode.Terminal {
  const openHandsTerminals = vscode.window.terminals.filter((terminal) =>
    terminal.name.startsWith("OpenHands"),
  );

  if (openHandsTerminals.length > 0) {
    // Use the most recent terminal, but only if we know it's idle
    const terminal = openHandsTerminals[openHandsTerminals.length - 1];

    // Only reuse terminals that we know are idle (safe to reuse)
    if (isKnownIdleTerminal(terminal)) {
      return terminal;
    }

    // If we don't know the terminal is idle, create a new one to avoid interrupting running processes
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
function executeOpenHandsCommand(
  terminal: vscode.Terminal,
  command: string,
): void {
  // Mark terminal as busy when we start a command
  markTerminalAsBusy(terminal.name);

  if (terminal.shellIntegration) {
    // Use Shell Integration for better control
    const execution = terminal.shellIntegration.executeCommand(command);

    // Monitor execution completion
    const disposable = vscode.window.onDidEndTerminalShellExecution((event) => {
      if (event.execution === execution) {
        if (event.exitCode === 0) {
          console.log("OpenHands command completed successfully");
          // Mark terminal as idle when command completes successfully
          markTerminalAsIdle(terminal.name);
        } else if (event.exitCode !== undefined) {
          console.log(`OpenHands command exited with code ${event.exitCode}`);
          // Mark terminal as idle even if command failed (user can reuse it)
          markTerminalAsIdle(terminal.name);
        }
        disposable.dispose(); // Clean up the event listener
      }
    });
  } else {
    // Fallback to traditional sendText
    terminal.sendText(command, true);
    // For traditional sendText, we can't track completion, so don't mark as idle
    // This means terminals without Shell Integration won't be reused, which is safer
  }
}

/**
 * Detects and builds virtual environment activation command
 * @returns string The activation command prefix (empty if no venv found)
 */
function detectVirtualEnvironment(): string {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    outputChannel.appendLine("DEBUG: No workspace folder found");
    return "";
  }

  const venvPaths = [".venv", "venv", ".virtualenv"];
  for (const venvPath of venvPaths) {
    const venvFullPath = path.join(workspaceFolder.uri.fsPath, venvPath);
    try {
      if (fs.existsSync(venvFullPath)) {
        const isWindows = process.platform === "win32";
        const activateScript = isWindows ? "Scripts\\activate" : "bin/activate";
        const activationCommand = `source "${venvFullPath}/${activateScript}" && `;
        outputChannel.appendLine(`DEBUG: Found venv at ${venvFullPath}`);
        return activationCommand;
      }
    } catch (error) {
      // Virtual environment doesn't exist, continue checking
    }
  }

  outputChannel.appendLine(
    `DEBUG: No venv found in workspace ${workspaceFolder.uri.fsPath}`,
  );
  return "";
}

/**
 * Builds the OpenHands command with proper sanitization
 * @param options Command options
 * @param activationCommand Virtual environment activation prefix
 * @returns string The complete command to execute
 */
function buildOpenHandsCommand(
  options: { task?: string; filePath?: string },
  activationCommand: string,
): string {
  let commandToSend = `${activationCommand}openhands`;

  if (options.filePath) {
    // Ensure filePath is properly quoted if it contains spaces or special characters
    const safeFilePath = options.filePath.includes(" ")
      ? `"${options.filePath}"`
      : options.filePath;
    commandToSend = `${activationCommand}openhands --file ${safeFilePath}`;
  } else if (options.task) {
    // Sanitize task string for command line (basic sanitization)
    // Replace backticks and double quotes that might break the command
    const sanitizedTask = options.task
      .replace(/`/g, "\\`")
      .replace(/"/g, '\\"');
    commandToSend = `${activationCommand}openhands --task "${sanitizedTask}"`;
  }

  return commandToSend;
}

/**
 * Main function to start OpenHands in terminal with safe terminal reuse
 * @param options Command options
 */
function startOpenHandsInTerminal(options: {
  task?: string;
  filePath?: string;
}): void {
  try {
    // Find or create terminal using safe detection
    const terminal = findOrCreateOpenHandsTerminal();
    terminal.show(true); // true to preserve focus on the editor

    // Detect virtual environment
    const activationCommand = detectVirtualEnvironment();

    // Build command
    const commandToSend = buildOpenHandsCommand(options, activationCommand);

    // Debug: show the actual command being sent
    outputChannel.appendLine(`DEBUG: Sending command: ${commandToSend}`);

    // Execute command using Shell Integration when available
    executeOpenHandsCommand(terminal, commandToSend);
  } catch (error) {
    vscode.window.showErrorMessage(`Error starting OpenHands: ${error}`);
  }
}

/**
 * Initialize runtime services for OpenHands backend communication
 * @param context VSCode extension context
 */
async function initializeRuntime(context: vscode.ExtensionContext): Promise<void> {
  try {
    // Get server URL from configuration
    const config = vscode.workspace.getConfiguration('openhands');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:3000');
    
    outputChannel.appendLine(`DEBUG: Initializing OpenHands runtime with server URL: ${serverUrl}`);
    
    // Initialize socket service
    socketService = new SocketService(serverUrl);
    
    // Initialize runtime action handler
    runtimeActionHandler = new VSCodeRuntimeActionHandler();
    runtimeActionHandler.setSocketService(socketService);
    
    // Set up event listener for incoming actions
    socketService.onEvent((event) => {
      if (runtimeActionHandler) {
        runtimeActionHandler.handleAction(event);
      }
    });
    
    // Attempt to connect to OpenHands backend
    // Note: This will only succeed if OpenHands backend is running
    try {
      await socketService.connect();
      outputChannel.appendLine('DEBUG: Successfully connected to OpenHands backend for runtime execution');
      vscode.window.showInformationMessage('OpenHands runtime connected - ready to execute actions in VSCode');
    } catch (error) {
      outputChannel.appendLine(`DEBUG: Could not connect to OpenHands backend: ${error}`);
      outputChannel.appendLine('DEBUG: Runtime will attempt to connect when OpenHands backend becomes available');
      // Don't show error to user - this is expected when backend isn't running
    }
    
  } catch (error) {
    outputChannel.appendLine(`ERROR: Failed to initialize OpenHands runtime: ${error}`);
    vscode.window.showErrorMessage(`Failed to initialize OpenHands runtime: ${error}`);
  }
}

/**
 * Clean up runtime services
 */
function cleanupRuntime(): void {
  if (socketService) {
    socketService.disconnect();
    socketService = null;
  }
  runtimeActionHandler = null;
  outputChannel.appendLine('DEBUG: OpenHands runtime services cleaned up');
}

export function activate(context: vscode.ExtensionContext) {
  // Initialize runtime services for OpenHands backend communication
  initializeRuntime(context);
  
  // Clean up terminal tracking when terminals are closed
  const terminalCloseDisposable = vscode.window.onDidCloseTerminal(
    (terminal) => {
      idleTerminals.delete(terminal.name);
    },
  );
  context.subscriptions.push(terminalCloseDisposable);

  // Command: Start New Conversation
  const startConversationDisposable = vscode.commands.registerCommand(
    "openhands.startConversation",
    () => {
      startOpenHandsInTerminal({});
    },
  );
  context.subscriptions.push(startConversationDisposable);

  // Command: Start Conversation with Active File Content
  const startWithFileContextDisposable = vscode.commands.registerCommand(
    "openhands.startConversationWithFileContext",
    () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        // No active editor, start conversation without task
        startOpenHandsInTerminal({});
        return;
      }

      if (editor.document.isUntitled) {
        const fileContent = editor.document.getText();
        if (!fileContent.trim()) {
          // Empty untitled file, start conversation without task
          startOpenHandsInTerminal({});
          return;
        }
        startOpenHandsInTerminal({ task: fileContent });
      } else {
        const filePath = editor.document.uri.fsPath;
        startOpenHandsInTerminal({ filePath });
      }
    },
  );
  context.subscriptions.push(startWithFileContextDisposable);

  // Command: Start Conversation with Selected Text
  const startWithSelectionContextDisposable = vscode.commands.registerCommand(
    "openhands.startConversationWithSelectionContext",
    () => {
      outputChannel.appendLine(
        "DEBUG: startConversationWithSelectionContext command triggered!",
      );
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        // No active editor, start conversation without task
        startOpenHandsInTerminal({});
        return;
      }
      if (editor.selection.isEmpty) {
        // No text selected, start conversation without task
        startOpenHandsInTerminal({});
        return;
      }
      const selectedText = editor.document.getText(editor.selection);
      startOpenHandsInTerminal({ task: selectedText });
    },
  );
  context.subscriptions.push(startWithSelectionContextDisposable);
}

export function deactivate() {
  // Clean up runtime services
  cleanupRuntime();
  
  // Clean up resources if needed, though for this simple extension,
  // VS Code handles terminal disposal.
}
