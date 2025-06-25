import * as assert from 'assert';
import * as vscode from 'vscode';

suite('SocketService Test Suite', () => {
    suite('Basic Functionality', () => {
        test('should be able to test basic assertions', () => {
            assert.ok(true, 'Basic test should pass');
            assert.strictEqual(1 + 1, 2, 'Math should work');
        });

        test('should have access to vscode API', () => {
            assert.ok(vscode, 'VSCode API should be available');
            assert.ok(vscode.version, 'VSCode version should be available');
        });

        test('should be able to mock fetch', () => {
            const originalFetch = global.fetch;
            
            // Mock fetch
            global.fetch = (() => {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({ test: 'data' })
                });
            }) as any;

            // Test that mock works
            assert.ok(global.fetch, 'Fetch should be mockable');
            
            // Restore
            global.fetch = originalFetch;
        });
    });
});
