import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as ChatSlice from "#/state/chat-slice";
import {
  updateStatusWhenErrorMessagePresent,
  WsClientProvider,
  useWsClient,
} from "#/context/ws-client-provider";
import { AuthProvider } from "#/context/auth-context";

describe("Propagate error message", () => {
  it("should do nothing when no message was passed from server", () => {
    const addErrorMessageSpy = vi.spyOn(ChatSlice, "addErrorMessage");
    updateStatusWhenErrorMessagePresent(null);
    updateStatusWhenErrorMessagePresent(undefined);
    updateStatusWhenErrorMessagePresent({});
    updateStatusWhenErrorMessagePresent({ message: null });

    expect(addErrorMessageSpy).not.toHaveBeenCalled();
  });

  it("should display error to user when present", () => {
    const message = "We have a problem!";
    const addErrorMessageSpy = vi.spyOn(ChatSlice, "addErrorMessage");
    updateStatusWhenErrorMessagePresent({ message });

    expect(addErrorMessageSpy).toHaveBeenCalledWith({
      message,
      status_update: true,
      type: "error",
    });
  });

  it("should display error including translation id when present", () => {
    const message = "We have a problem!";
    const addErrorMessageSpy = vi.spyOn(ChatSlice, "addErrorMessage");
    updateStatusWhenErrorMessagePresent({
      message,
      data: { msg_id: "..id.." },
    });

    expect(addErrorMessageSpy).toHaveBeenCalledWith({
      message,
      id: "..id..",
      status_update: true,
      type: "error",
    });
  });
});

// Create a mock for socket.io-client
const mockEmit = vi.fn();
const mockOn = vi.fn();
const mockOff = vi.fn();
const mockDisconnect = vi.fn();

vi.mock("socket.io-client", () => ({
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
}));

// Mock component to test the hook
function TestComponent() {
  const { send } = useWsClient();

  React.useEffect(() => {
    // Send a test event
    send({ type: "test_event" });
  }, [send]);

  return <div>Test Component</div>;
}

describe("WsClientProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should emit oh_user_action event when send is called", async () => {
    const { getByText } = render(<TestComponent />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          <AuthProvider initialProviderTokens={[]}>
            <WsClientProvider conversationId="test-conversation-id">
              {children}
            </WsClientProvider>
          </AuthProvider>
        </QueryClientProvider>
      ),
    });

    // Assert
    expect(getByText("Test Component")).toBeInTheDocument();

    // Wait for the emit call to happen (useEffect needs time to run)
    await waitFor(
      () => {
        expect(mockEmit).toHaveBeenCalledWith("oh_user_action", {
          type: "test_event",
        });
      },
      { timeout: 1000 },
    );
  });
});
