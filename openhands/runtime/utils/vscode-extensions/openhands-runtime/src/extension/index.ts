import * as vscode from 'vscode';
import { SocketService } from './services/socket-service';
import { VSCodeRuntimeActionHandler } from './services/vscodeRuntimeActionHandler';
import { OpenHandsActionEvent, OpenHandsObservationEvent, OpenHandsEventType, isOpenHandsAction } from '@openhands/types';

export function activate(context: vscode.ExtensionContext) {
    console.log('OpenHands VSCode Runtime extension is now active.');

    // Get configuration
    const config = vscode.workspace.getConfiguration('openhands');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:3000');

    // Initialize services
    const socketService = new SocketService(serverUrl);
    const actionHandler = new VSCodeRuntimeActionHandler();
    actionHandler.setSocketService(socketService);

    // Start the socket connection and set up action handling
    socketService.connect().then(() => {
        socketService.onEvent((event) => {
            if (isOpenHandsAction(event)) {
                actionHandler.handleAction(event);
            }
        });
    }).catch((error) => {
        console.error('Failed to connect to OpenHands backend:', error);
    });

    // Register disposables
    context.subscriptions.push({
        dispose: () => {
            socketService.disconnect();
            console.log('OpenHands VSCode Runtime extension deactivated.');
        }
    });
}

export function deactivate() {
    // Cleanup is handled by the disposable in activate
}
