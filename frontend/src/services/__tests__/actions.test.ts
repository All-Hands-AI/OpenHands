import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { handleStatusMessage } from "../actions";
import { StatusMessage } from "#/types/message";
import { queryClient } from "#/query-client-config";
import store from "#/store";
import { setCurStatusMessage } from "#/state/status-slice";
import { trackError } from "#/utils/error-handler";

// Mock dependencies
vi.mock("#/query-client-config", () => ({
  queryClient: {
    invalidateQueries: vi.fn(),
  },
}));

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

vi.mock("#/state/status-slice", () => ({
  setCurStatusMessage: vi.fn(),
}));

vi.mock("#/state/chat-slice", () => ({
  addErrorMessage: vi.fn(),
}));

vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

describe("handleStatusMessage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should invalidate queries when receiving a conversation title update", () => {
    // Create a status message with a conversation title
    const statusMessage: StatusMessage = {
      status_update: true,
      type: "info",
      message: "conversation-123",
      conversation_title: "New Conversation Title",
    };

    // Call the function
    handleStatusMessage(statusMessage);

    // Verify that queryClient.invalidateQueries was called with the correct parameters
    expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["user", "conversation", "conversation-123"],
    });

    // Verify that store.dispatch was not called
    expect(store.dispatch).not.toHaveBeenCalled();
  });

  it("should dispatch setCurStatusMessage for info messages without conversation_title", () => {
    // Create a status message without a conversation title
    const statusMessage: StatusMessage = {
      status_update: true,
      type: "info",
      message: "Some info message",
    };

    // Call the function
    handleStatusMessage(statusMessage);

    // Verify that store.dispatch was called with setCurStatusMessage
    expect(store.dispatch).toHaveBeenCalledWith(
      setCurStatusMessage(statusMessage),
    );

    // Verify that queryClient.invalidateQueries was not called
    expect(queryClient.invalidateQueries).not.toHaveBeenCalled();
  });

  it("should dispatch addErrorMessage for error messages", () => {
    // Create an error status message
    const statusMessage: StatusMessage = {
      status_update: true,
      type: "error",
      id: "ERROR_ID",
      message: "Some error message",
    };

    // Call the function
    handleStatusMessage(statusMessage);

    // Verify that trackError was called with the correct parameters
    expect(trackError).toHaveBeenCalledWith({
      message: "Some error message",
      source: "chat",
      metadata: { msgId: "ERROR_ID" },
    });

    // Verify that queryClient.invalidateQueries was not called
    expect(queryClient.invalidateQueries).not.toHaveBeenCalled();
  });
});
