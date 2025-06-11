import { io, Socket } from 'socket.io-client';

interface OpenHandsEvent {
    id: string;
    action?: string;
    args?: any;
    observation?: string;
    content?: string;
    extras?: any;
    message?: string;
    source?: string;
    cause?: string;
    timestamp?: string;
}

export class SocketService {
    private socket: Socket | null = null;
    private serverUrl: string;
    private conversationId: string | null = null;
    private eventListeners: Array<(event: OpenHandsEvent) => void> = [];

    constructor(serverUrl: string) {
        this.serverUrl = serverUrl;
    }

    async connect(): Promise<void> {
        // First, initialize a conversation via HTTP API
        try {
            const response = await fetch(`${this.serverUrl}/api/conversations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ initial_user_msg: 'VSCode Runtime Connection' }),
            });

            if (!response.ok) {
                throw new Error(`Failed to initialize conversation: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            this.conversationId = data.conversation_id;

            // Now connect via Socket.IO
            this.socket = io(this.serverUrl, {
                query: {
                    conversation_id: this.conversationId,
                    latest_event_id: '-1',
                },
            });

            this.socket.on('connect', () => {
                console.log('Connected to OpenHands backend via Socket.IO');
            });

            this.socket.on('oh_event', (event: OpenHandsEvent) => {
                console.log('Received event:', event);
                this.eventListeners.forEach(listener => listener(event));
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from OpenHands backend');
            });

            this.socket.on('error', (error: any) => {
                console.error('Socket.IO error:', error);
            });

            this.socket.on('connect_error', (error: any) => {
                console.error('Socket.IO connection error:', error);
            });
        } catch (error) {
            console.error('Error connecting to OpenHands backend:', error);
            throw error;
        }
    }

    disconnect(): void {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            console.log('Socket.IO connection closed');
        }
    }

    onEvent(listener: (event: OpenHandsEvent) => void): void {
        this.eventListeners.push(listener);
    }

    sendEvent(event: OpenHandsEvent): void {
        if (this.socket && this.socket.connected) {
            this.socket.emit('oh_event', event);
            console.log('Sent event:', event);
        } else {
            console.error('Cannot send event: Socket is not connected');
        }
    }
}
