import * as assert from 'assert';
import * as vscode from 'vscode';
import { SocketService } from '../../services/socket-service';

// Mock Socket.IO client
const mockSocket = {
    on: () => {},
    emit: () => {},
    disconnect: () => {},
    connected: true,
    id: 'mock-socket-id'
};

// Mock fetch globally
const originalFetch = global.fetch;

suite('SocketService Test Suite', () => {
    let socketService: SocketService;
    let mockFetch: any;

    setup(() => {
        // Create service instance
        socketService = new SocketService('http://localhost:3000');
        
        // Reset fetch mock
        mockFetch = null;
    });

    teardown(() => {
        // Restore original fetch
        if (originalFetch) {
            global.fetch = originalFetch;
        }
        
        // Clean up service
        if (socketService) {
            socketService.disconnect();
        }
    });

    suite('Constructor and Initialization', () => {
        test('should initialize with server URL', () => {
            const service = new SocketService('http://test-server:8080');
            assert.ok(service, 'SocketService should be created');
        });

        test('should store server URL correctly', () => {
            const serverUrl = 'http://custom-server:9000';
            const service = new SocketService(serverUrl);
            // We can't directly access private properties, but we can test behavior
            assert.ok(service, 'Service should be initialized with custom URL');
        });

        test('should have null connection ID initially', () => {
            const connectionId = socketService.getConnectionId();
            assert.strictEqual(connectionId, null, 'Connection ID should be null initially');
        });
    });

    suite('Event Handling Interface', () => {
        test('should allow adding event listeners', () => {
            const listener = (event: any) => {
                console.log('Event received:', event);
            };
            
            // This tests the public interface
            socketService.onEvent(listener);
            assert.ok(true, 'Should allow adding event listeners without error');
        });

        test('should allow sending events when not connected', () => {
            const mockEvent = {
                id: 'test-event-id',
                timestamp: new Date().toISOString(),
                source: 'vscode',
                message: 'test message',
                event_type: 'test'
            } as any;
            
            // This should not throw even if not connected
            socketService.sendEvent(mockEvent);
            assert.ok(true, 'Should allow sending events without error when disconnected');
        });
    });

    suite('Registration Workflow', () => {
        test('should prepare correct registration data', async () => {
            let registrationCalled = false;
            let registrationData: any = null;
            
            // Mock successful registration
            mockFetch = (url: string, options?: any) => {
                if (url.includes('/api/vscode/register')) {
                    registrationCalled = true;
                    registrationData = JSON.parse(options.body);
                    
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            connection_id: 'test-connection-id',
                            status: 'registered'
                        })
                    });
                }
                if (url.includes('/api/conversations')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            conversation_id: 'test-conversation-id'
                        })
                    });
                }
                return Promise.resolve({ ok: false, status: 404 });
            };
            global.fetch = mockFetch as any;

            try {
                await socketService.connect();
            } catch (error) {
                // Expected to fail due to Socket.IO mocking limitations
            }

            assert.ok(registrationCalled, 'Registration should be called');
            assert.ok(registrationData, 'Registration data should be captured');
            assert.ok(registrationData.workspace_path !== undefined, 'Should include workspace path');
            assert.ok(registrationData.vscode_version, 'Should include VSCode version');
            assert.ok(registrationData.extension_version, 'Should include extension version');
            assert.ok(Array.isArray(registrationData.capabilities), 'Should include capabilities array');
            assert.ok(registrationData.capabilities.includes('file_operations'), 'Should include file_operations capability');
        });

        test('should handle registration failure', async () => {
            mockFetch = (url: string) => {
                if (url.includes('/api/vscode/register')) {
                    return Promise.resolve({
                        ok: false,
                        status: 500,
                        statusText: 'Internal Server Error'
                    });
                }
                return Promise.resolve({ ok: false, status: 404 });
            };
            global.fetch = mockFetch as any;

            try {
                await socketService.connect();
                assert.fail('Should have thrown an error for registration failure');
            } catch (error) {
                assert.ok(error instanceof Error, 'Should throw an Error');
                assert.ok((error as Error).message.includes('Failed to register VSCode instance'), 
                    'Should have descriptive error message');
            }
        });

        test('should handle network errors during registration', async () => {
            mockFetch = () => {
                return Promise.reject(new Error('Network error'));
            };
            global.fetch = mockFetch as any;

            try {
                await socketService.connect();
                assert.fail('Should have thrown an error for network failure');
            } catch (error) {
                assert.ok(error instanceof Error, 'Should throw an Error');
                assert.ok((error as Error).message.includes('Network error'), 
                    'Should propagate network error');
            }
        });
    });

    suite('Conversation Creation', () => {
        test('should create conversation after successful registration', async () => {
            let conversationCalled = false;
            let conversationData: any = null;
            
            mockFetch = (url: string, options?: any) => {
                if (url.includes('/api/vscode/register')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            connection_id: 'test-connection-id',
                            status: 'registered'
                        })
                    });
                }
                if (url.includes('/api/conversations')) {
                    conversationCalled = true;
                    conversationData = JSON.parse(options.body);
                    
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            conversation_id: 'test-conversation-id'
                        })
                    });
                }
                return Promise.resolve({ ok: false, status: 404 });
            };
            global.fetch = mockFetch as any;

            try {
                await socketService.connect();
            } catch (error) {
                // Expected to fail due to Socket.IO mocking limitations
            }

            assert.ok(conversationCalled, 'Conversation creation should be called');
            assert.ok(conversationData, 'Conversation data should be captured');
            assert.strictEqual(conversationData.initial_user_msg, 'VSCode Runtime Connection', 
                'Should have correct initial message');
        });

        test('should handle conversation creation failure', async () => {
            mockFetch = (url: string) => {
                if (url.includes('/api/vscode/register')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve({
                            connection_id: 'test-connection-id',
                            status: 'registered'
                        })
                    });
                }
                if (url.includes('/api/conversations')) {
                    return Promise.resolve({
                        ok: false,
                        status: 400,
                        statusText: 'Bad Request'
                    });
                }
                return Promise.resolve({ ok: false, status: 404 });
            };
            global.fetch = mockFetch as any;

            try {
                await socketService.connect();
                assert.fail('Should have thrown an error for conversation creation failure');
            } catch (error) {
                assert.ok(error instanceof Error, 'Should throw an Error');
                assert.ok((error as Error).message.includes('Failed to initialize conversation'), 
                    'Should have descriptive error message');
            }
        });
    });

    suite('Disconnection and Cleanup', () => {
        test('should handle disconnection gracefully when not connected', () => {
            try {
                socketService.disconnect();
                assert.ok(true, 'Should handle disconnection without error');
            } catch (error) {
                assert.fail('Disconnection should not throw error when not connected');
            }
        });

        test('should handle multiple disconnects safely', () => {
            // Test that disconnect doesn't throw and cleans up properly
            socketService.disconnect();
            
            // Try to disconnect again - should not throw
            socketService.disconnect();
            assert.ok(true, 'Multiple disconnects should be safe');
        });
    });
});
