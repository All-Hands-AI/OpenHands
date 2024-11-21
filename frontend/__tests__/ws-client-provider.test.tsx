import { render, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { WsClientProvider } from "../src/context/ws-client-provider";
import { Settings } from "../src/services/settings";
import ActionType from "../src/types/ActionType";

// Mock WebSocket
class MockWebSocket {
  private listeners: { [key: string]: ((event: any) => void)[] } = {};
  public readyState = WebSocket.OPEN;
  public send = vi.fn();

  constructor() {
    // Mock implementation
  }

  addEventListener(event: string, callback: (event: any) => void) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  removeEventListener(event: string, callback: (event: any) => void) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  // Helper to trigger events
  triggerEvent(event: string, data?: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.triggerEvent('close');
  }
}

// Mock window.WebSocket
let mockWsInstance: MockWebSocket;
const mockWebSocket = vi.fn().mockImplementation(() => {
  mockWsInstance = new MockWebSocket();
  return mockWsInstance;
});
vi.stubGlobal('WebSocket', mockWebSocket);

// Mock EventLogger
vi.mock('#/utils/event-logger', () => ({
  default: {
    error: vi.fn(),
    event: vi.fn(),
  },
}));

// Mock posthog
vi.mock('posthog-js', () => ({
  default: {
    capture: vi.fn(),
  },
}));

describe('WsClientProvider', () => {
  let ws: MockWebSocket;

  beforeEach(() => {
    vi.clearAllMocks();
    mockWsInstance = undefined as any;
  });

  it('sends INIT event only on new session, not on reconnection', async () => {
    const settings: Settings = {
      model: 'test-model',
      provider: 'test-provider',
      temperature: 0.7,
      max_tokens: 1000,
      top_p: 1,
      frequency_penalty: 0,
      presence_penalty: 0,
    };

    // Initial render - should send INIT
    const { rerender } = render(
      <WsClientProvider
        enabled={true}
        token="test-token"
        ghToken="test-gh-token"
        settings={settings}
      >
        <div>Test</div>
      </WsClientProvider>
    );

    // Wait for the component to mount and create WebSocket
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Get the WebSocket instance
    ws = mockWsInstance;

    // Trigger open event
    await act(async () => {
      ws.triggerEvent('open');
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Verify INIT was sent
    expect(ws.send).toHaveBeenCalledWith(
      JSON.stringify({
        action: ActionType.INIT,
        args: settings,
      })
    );

    // Clear the mock to check next calls
    ws.send.mockClear();

    // Add a mock event to simulate existing session
    await act(async () => {
      ws.triggerEvent('message', { data: JSON.stringify({ id: 1, action: 'test' }) });
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Simulate reconnection by re-rendering
    rerender(
      <WsClientProvider
        enabled={true}
        token="test-token"
        ghToken="test-gh-token"
        settings={settings}
      >
        <div>Test</div>
      </WsClientProvider>
    );

    // Wait for the component to re-mount and create new WebSocket
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Trigger open event again
    await act(async () => {
      ws.triggerEvent('open');
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Verify INIT was not sent on reconnection
    expect(ws.send).not.toHaveBeenCalled();
  });
});
