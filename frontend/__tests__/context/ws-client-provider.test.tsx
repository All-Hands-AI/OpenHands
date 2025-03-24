import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithQueryClient } from "../utils/test-utils";
import {
  updateStatusWhenErrorMessagePresent,
  WsClientProvider,
  useWsClient,
} from "#/context/ws-client-provider";
import React from "react";
import * as observations from "#/services/observations";

// Create a mock for the addErrorMessage function
const mockAddErrorMessage = vi.fn();

// Mock the getChatFunctions method
vi.spyOn(observations, "getChatFunctions").mockImplementation(() => ({
  addErrorMessage: mockAddErrorMessage,
  addAssistantMessage: vi.fn(),
  addAssistantAction: vi.fn(),
  addAssistantObservation: vi.fn(),
  addUserMessage: vi.fn(),
  clearMessages: vi.fn(),
  messages: [],
  isLoading: false,
}));

describe("Propagate error message", () => {
  beforeEach(() => {
    // Reset the mocks before each test
    vi.clearAllMocks();
    // We no longer need to mock Redux actions
  });

  it("should do nothing when no message was passed from server", () => {
    updateStatusWhenErrorMessagePresent(null)
    updateStatusWhenErrorMessagePresent(undefined)
    updateStatusWhenErrorMessagePresent({})
    updateStatusWhenErrorMessagePresent({message: null})

    expect(mockAddErrorMessage).not.toHaveBeenCalled();
  });

  it("should display error to user when present", () => {
    const message = "We have a problem!"
    updateStatusWhenErrorMessagePresent({message})

    expect(mockAddErrorMessage).toHaveBeenCalledWith({
      message,
      status_update: true,
      type: 'error'
     });
  });

  it("should display error including translation id when present", () => {
    const message = "We have a problem!"
    updateStatusWhenErrorMessagePresent({message, data: {msg_id: '..id..'}})

    expect(mockAddErrorMessage).toHaveBeenCalledWith({
      message,
      id: '..id..',
      status_update: true,
      type: 'error'
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
    const { getByText } = renderWithQueryClient(
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
