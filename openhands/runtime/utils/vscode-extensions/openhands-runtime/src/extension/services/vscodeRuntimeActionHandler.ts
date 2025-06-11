import * as vscode from 'vscode';
import { SocketService } from './socket-service';
import { OpenHandsActionEvent, OpenHandsEventType, OpenHandsObservationEvent, OpenHandsParsedEvent, isOpenHandsAction } from '@openhands/types';

export class VSCodeRuntimeActionHandler {
    private workspacePath: string | undefined;
    private socketService: SocketService | null = null;

    constructor() {
        // Determine the workspace path for security restrictions
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders && workspaceFolders.length > 0) {
            this.workspacePath = workspaceFolders[0].uri.fsPath;
            console.log(`Workspace path set to: ${this.workspacePath}`);
        } else {
            console.warn('No workspace folder found. File operations will be restricted.');
        }
    }

    setSocketService(socketService: SocketService): void {
        this.socketService = socketService;
        console.log('SocketService set for VSCodeRuntimeActionHandler');
    }

    private sanitizePath(filePath: string): string | null {
        if (!this.workspacePath) {
            console.error('No workspace path defined. Blocking file operation for security.');
            return null;
        }

        // Handle absolute and relative paths
        let resolvedPath = filePath;
        if (!filePath.startsWith('/')) {
            resolvedPath = `${this.workspacePath}/${filePath}`;
        }

        // Basic check to prevent path traversal
        if (!resolvedPath.startsWith(this.workspacePath)) {
            console.error(`Path traversal attempt detected. Path ${resolvedPath} is outside workspace ${this.workspacePath}.`);
            return null;
        }

        return resolvedPath;
    }

    private async openOrFocusFile(filePath: string): Promise<void> {
        try {
            const uri = vscode.Uri.file(filePath);
            const document = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(document);
        } catch (error) {
            console.error(`Failed to open file ${filePath}:`, error);
        }
    }

    handleAction(event: OpenHandsParsedEvent): void {
        if (!isOpenHandsAction(event) || !event.args) {
            console.error('Invalid event received for action handling:', event);
            return;
        }

        console.log(`Handling action: ${event.action} with args:`, event.args);

        switch (event.action) {
            case 'run':
                this.handleRunAction(event);
                break;
            case 'read':
                this.handleReadAction(event);
                break;
            case 'write':
                this.handleWriteAction(event);
                break;
            case 'edit':
                this.handleEditAction(event);
                break;
            default:
                console.warn(`Unsupported action received: ${event.action}`);
                this.sendErrorObservation(event, `Unsupported action: ${event.action}`);
        }
    }

    private sendObservation(event: OpenHandsParsedEvent, observationType: string, content: string, extras: Record<string, unknown> = {}, error: boolean = false): void {
        const observationEvent: OpenHandsObservationEvent<OpenHandsEventType> = {
            id: Date.now(),
            observation: observationType as OpenHandsEventType,
            content: content,
            extras: extras,
            message: error ? `Error during ${observationType} operation` : `VSCode executed ${observationType} operation`,
            source: 'environment',
            cause: -1,
            timestamp: new Date().toISOString()
        };
        if ('id' in event && typeof event.id === 'number') {
            observationEvent.cause = event.id;
        }

        if (this.socketService) {
            this.socketService.sendEvent(observationEvent as unknown as OpenHandsParsedEvent);
        } else {
            console.error('Cannot send observation: SocketService is not set');
            console.log('Observation that would have been sent:', observationEvent);
        }
    }

    private sendErrorObservation(event: OpenHandsParsedEvent, errorMessage: string): void {
        this.sendObservation(event, 'action' in event ? event.action || 'unknown' : 'unknown', errorMessage, {}, true);
    }

    private handleRunAction(event: OpenHandsParsedEvent): void {
        if (!isOpenHandsAction(event) || event.action !== 'run') {
            this.sendErrorObservation(event, 'Invalid event type for run action');
            return;
        }
        const args = event.args as Record<string, unknown>;
        const command = args.command as string | undefined;
        if (!command) {
            this.sendErrorObservation(event, 'No command provided for run action');
            return;
        }

        // Create or get a terminal for OpenHands commands
        const terminalName = 'OpenHands Runtime';
        let terminal = vscode.window.terminals.find(t => t.name === terminalName);
        if (!terminal) {
            terminal = vscode.window.createTerminal(terminalName);
        }
        terminal.show(true); // Show the terminal but preserve focus on editor

        // Send the command to the terminal
        terminal.sendText(command);

        // For now, we can't reliably capture terminal output programmatically
        // So we'll send a placeholder observation
        this.sendObservation(event, 'run', `Command '${command}' sent to terminal. Output will be visible in the '${terminalName}' terminal.`, { command: command, exit_code: 0 });
    }

    private async handleReadAction(event: OpenHandsParsedEvent): Promise<void> {
        if (!isOpenHandsAction(event) || event.action !== 'read') {
            this.sendErrorObservation(event, 'Invalid event type for read action');
            return;
        }
        const args = event.args as { path?: string };
        const filePath = args.path;
        if (!filePath) {
            this.sendErrorObservation(event, 'No path provided for read action');
            return;
        }

        const sanitizedPath = this.sanitizePath(filePath);
        if (!sanitizedPath) {
            this.sendErrorObservation(event, `Invalid path: ${filePath}. Path resolves outside the workspace.`);
            return;
        }

        try {
            const uri = vscode.Uri.file(sanitizedPath);
            const contentBuffer = await vscode.workspace.fs.readFile(uri);
            const content = contentBuffer.toString();
            this.sendObservation(event, 'read', content, { path: filePath });
            // Optionally open the file in the editor for viewing
            await this.openOrFocusFile(sanitizedPath);
        } catch (error) {
            console.error(`Error reading file ${sanitizedPath}:`, error);
            this.sendErrorObservation(event, `Error reading file ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private async handleWriteAction(event: OpenHandsParsedEvent): Promise<void> {
        if (!isOpenHandsAction(event) || event.action !== 'write') {
            this.sendErrorObservation(event, 'Invalid event type for write action');
            return;
        }
        const args = event.args as { path: string; content: string };
        const filePath = args.path;
        const content = args.content;
        if (!filePath || content === undefined) {
            this.sendErrorObservation(event, 'Missing path or content for write action');
            return;
        }

        const sanitizedPath = this.sanitizePath(filePath);
        if (!sanitizedPath) {
            this.sendErrorObservation(event, `Invalid path: ${filePath}. Path resolves outside the workspace.`);
            return;
        }

        try {
            const uri = vscode.Uri.file(sanitizedPath);
            const contentBuffer = new TextEncoder().encode(content);
            await vscode.workspace.fs.writeFile(uri, contentBuffer);
            this.sendObservation(event, 'write', `File ${filePath} written successfully`, { path: filePath });
            // Open the file in the editor for viewing
            await this.openOrFocusFile(sanitizedPath);
        } catch (error) {
            console.error(`Error writing to file ${sanitizedPath}:`, error);
            this.sendErrorObservation(event, `Error writing to file ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private async handleEditAction(event: OpenHandsParsedEvent): Promise<void> {
        if (!isOpenHandsAction(event) || event.action !== 'edit') {
            this.sendErrorObservation(event, 'Invalid event type for edit action');
            return;
        }
        const args = event.args as { path: string; content: string };
        const filePath = args.path;
        const newContent = args.content;
        if (!filePath || newContent === undefined) {
            this.sendErrorObservation(event, 'Missing path or content for edit action');
            return;
        }

        const sanitizedPath = this.sanitizePath(filePath);
        if (!sanitizedPath) {
            this.sendErrorObservation(event, `Invalid path: ${filePath}. Path resolves outside the workspace.`);
            return;
        }

        try {
            const uri = vscode.Uri.file(sanitizedPath);
            // Read the current content to potentially show a diff
            let oldContent = '';
            try {
                const currentContentBuffer = await vscode.workspace.fs.readFile(uri);
                oldContent = currentContentBuffer.toString();
            } catch (error) {
                console.warn(`Could not read current content of ${filePath} for diff, file might not exist yet.`, error);
            }

            // Write the new content
            const contentBuffer = new TextEncoder().encode(newContent);
            await vscode.workspace.fs.writeFile(uri, contentBuffer);

            // Open or focus the file to show changes
            await this.openOrFocusFile(sanitizedPath);

            this.sendObservation(event, 'edit', `File ${filePath} edited successfully`, { path: filePath, old_content: oldContent, new_content: newContent });
        } catch (error) {
            console.error(`Error editing file ${sanitizedPath}:`, error);
            this.sendErrorObservation(event, `Error editing file ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
}
