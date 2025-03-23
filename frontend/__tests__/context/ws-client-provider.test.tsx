import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import * as ErrorHandler from "#/utils/error-handler";
import {
  updateStatusWhenErrorMessagePresent,
  WsClientProvider,
  useWsClient,
} from "#/context/ws-client-provider";
import React from "react";

describe("Propagate error message", () => {
  it("should do nothing when no message was passed from server", () => {
    const showChatErrorSpy = vi.spyOn(ErrorHandler, "showChatError");
    updateStatusWhenErrorMessagePresent(null)
    updateStatusWhenErrorMessagePresent(undefined)
    updateStatusWhenErrorMessagePresent({})
    updateStatusWhenErrorMessagePresent({message: null})

    expect(showChatErrorSpy).not.toHaveBeenCalled();
  });

  it("should display error to user when present", () => {
    const message = "We have a problem!"
    const showChatErrorSpy = vi.spyOn(ErrorHandler, "showChatError")
    updateStatusWhenErrorMessagePresent({message})

    expect(showChatErrorSpy).toHaveBeenCalledWith({
      message,
      source: "websocket",
      metadata: {},
      msgId: undefined
     });
  });

  it("should display error including translation id when present", () => {
    const message = "We have a problem!"
    const showChatErrorSpy = vi.spyOn(ErrorHandler, "showChatError")
    updateStatusWhenErrorMessagePresent({message, data: {msg_id: '..id..'}})

    expect(showChatErrorSpy).toHaveBeenCalledWith({
      message,
      source: "websocket",
      metadata: {msg_id: '..id..'},
      msgId: '..id..'
     });
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
    const { getByText } = render(
      <WsClientProvider conversationId="test-conversation-id">
        <TestComponent />
      </WsClientProvider>
    );

    // Assert
    expect(getByText("Test Component")).toBeInTheDocument();

    // Wait for the emit call to happen (useEffect needs time to run)
    await waitFor(() => {
      expect(mockEmit).toHaveBeenCalledWith("oh_user_action", { type: "test_event" });
    }, { timeout: 1000 });
  });
});
