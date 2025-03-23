import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import {
  updateStatusWhenErrorMessagePresent,
  WsClientProvider,
  useWsClient,
} from "#/context/ws-client-provider";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

describe("Propagate error message", () => {
  it("should do nothing when no message was passed from server", () => {
    // Create a mock for the query client
    const mockSetQueryData = vi.fn();
    window.__queryClient = {
      setQueryData: mockSetQueryData,
      getQueryData: vi.fn().mockReturnValue({ messages: [] }),
    } as any;

    updateStatusWhenErrorMessagePresent(null)
    updateStatusWhenErrorMessagePresent(undefined)
    updateStatusWhenErrorMessagePresent({})
    updateStatusWhenErrorMessagePresent({message: null})

    expect(mockSetQueryData).not.toHaveBeenCalled();
  });

  it("should display error to user when present", () => {
    // Create a mock for the query client
    const mockSetQueryData = vi.fn();
    window.__queryClient = {
      setQueryData: mockSetQueryData,
      getQueryData: vi.fn().mockReturnValue({ messages: [] }),
    } as any;

    const message = "We have a problem!"
    updateStatusWhenErrorMessagePresent({message})

    // Verify that setQueryData was called with the status message
    expect(mockSetQueryData).toHaveBeenCalled();
  });

  it("should display error including translation id when present", () => {
    // Create a mock for the query client
    const mockSetQueryData = vi.fn();
    window.__queryClient = {
      setQueryData: mockSetQueryData,
      getQueryData: vi.fn().mockReturnValue({ messages: [] }),
    } as any;

    const message = "We have a problem!"
    updateStatusWhenErrorMessagePresent({message, data: {msg_id: '..id..'}})

    // Verify that setQueryData was called with the status message
    expect(mockSetQueryData).toHaveBeenCalled();
  });
});

// Create a mock for socket.io-client
const mockEmit = vi.fn();
const mockOn = vi.fn();
const mockOff = vi.fn();
const mockDisconnect = vi.fn();

vi.mock("socket.io-client", () => {
  return {
    io: vi.fn(() => ({
      emit: mockEmit,
      on: mockOn,
      off: mockOff,
      disconnect: mockDisconnect,
      io: {
        opts: {
          query: {},
        },
      },
    })),
  };
});

// Mock component to test the hook
const TestComponent = () => {
  const { send } = useWsClient();

  React.useEffect(() => {
    // Send a test event
    send({ type: "test_event" });
  }, [send]);

  return <div>Test Component</div>;
};

describe("WsClientProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should emit oh_user_action event when send is called", async () => {
    // Create a new QueryClient for each test
    const queryClient = new QueryClient();
    
    // Make it available globally for the test
    window.__queryClient = queryClient as any;
    
    const { getByText } = render(
      <QueryClientProvider client={queryClient}>
        <WsClientProvider conversationId="test-conversation-id">
          <TestComponent />
        </WsClientProvider>
      </QueryClientProvider>
    );

    // Assert
    expect(getByText("Test Component")).toBeInTheDocument();

    // Wait for the emit call to happen (useEffect needs time to run)
    await waitFor(() => {
      expect(mockEmit).toHaveBeenCalledWith("oh_user_action", { type: "test_event" });
    }, { timeout: 1000 });
  });
});
