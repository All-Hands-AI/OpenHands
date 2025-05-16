import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { TerminalStreamService } from "#/services/terminal-stream-service";
import store from "#/store";

// Mock Redux store
vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

// Mock parseTerminalOutput
vi.mock("#/utils/parse-terminal-output", () => ({
  parseTerminalOutput: vi.fn((input) => input),
}));

describe("TerminalStreamService", () => {
  let service: TerminalStreamService;
  let mockEventSource: any;
  
  // Mock EventSource
  class MockEventSource {
    onopen: (() => void) | null = null;
    onmessage: ((event: any) => void) | null = null;
    onerror: ((error: any) => void) | null = null;
    
    constructor(public url: string) {
      mockEventSource = this;
    }
    
    close() {
      // Mock close method
    }
  }
  
  beforeEach(() => {
    // Save original EventSource
    const originalEventSource = global.EventSource;
    
    // Mock EventSource
    global.EventSource = MockEventSource as any;
    
    // Create service
    service = new TerminalStreamService("http://localhost:8000");
    
    // Reset mocks
    vi.clearAllMocks();
    
    return () => {
      // Restore original EventSource
      global.EventSource = originalEventSource;
    };
  });
  
  afterEach(() => {
    service.disconnect();
  });
  
  it("should connect to the terminal stream", () => {
    service.connect();
    
    expect(mockEventSource.url).toBe("http://localhost:8000/terminal-stream");
  });
  
  it("should handle partial stream chunks", () => {
    service.connect();
    
    // Simulate connection open
    if (mockEventSource.onopen) {
      mockEventSource.onopen();
    }
    
    // Simulate message event
    if (mockEventSource.onmessage) {
      mockEventSource.onmessage({
        data: JSON.stringify({
          content: "Hello, world!",
          metadata: {
            command: "echo Hello, world!",
            is_complete: false,
            timestamp: Date.now(),
            command_id: 123,
          },
        }),
      });
    }
    
    // Check if store.dispatch was called with appendOutput
    expect(store.dispatch).toHaveBeenCalledWith({
          type: "command/appendOutput",
            payload: expect.objectContaining({
                isPartial: true,
                content: "Hello, world!",
            }),
      })
  });

    it("should handle full command output", () => {
        service.connect();

        // Simulate connection open
        if (mockEventSource.onopen) {
            mockEventSource.onopen();
        }

        // Simulate message event
        if (mockEventSource.onmessage) {
            mockEventSource.onmessage({
                data: JSON.stringify({
                    content: "Hello, world!",
                    metadata: {
                        command: "echo Hello, world!",
                        is_complete: true,
                        timestamp: Date.now(),
                        command_id: 123,
                    },
                }),
            });
        }

        // Check if store.dispatch was called with appendOutput
        expect(store.dispatch).toHaveBeenCalledWith({
            type: "command/appendOutput",
            payload: expect.objectContaining({
                isPartial: false,
                content: "Hello, world!",
            }),
        })
    });
  
  it("should handle connection errors", () => {
    // Spy on console.error
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    
    service.connect();
    
    // Simulate error event
    if (mockEventSource.onerror) {
      mockEventSource.onerror(new Error("Connection error"));
    }
    
    // Check if console.error was called
    expect(consoleErrorSpy).toHaveBeenCalled();
    
    // Restore console.error
    consoleErrorSpy.mockRestore();
  });
  
  it("should disconnect from the terminal stream", () => {
    service.connect();
    
    // Spy on EventSource.close
    const closeSpy = vi.spyOn(mockEventSource, "close");
    
    service.disconnect();
    
    expect(closeSpy).toHaveBeenCalled();
    expect(service.isStreamConnected()).toBe(false);
  });
});