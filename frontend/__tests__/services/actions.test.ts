import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleStatusMessage, handleActionMessage } from "#/services/actions";
import store from "#/store";
import { trackError } from "#/utils/error-handler";
import ActionType from "#/types/action-type";

// Mock dependencies
vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
    it("should dispatch info messages to status state", () => {
      const message = {
        type: "info",
        message: "Runtime is not available",
        id: "runtime.unavailable",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(store.dispatch).toHaveBeenCalledWith(expect.objectContaining({
        payload: message,
      }));
    });

    it("should log error messages and display them in chat", () => {
      const message = {
        type: "error",
        message: "Runtime connection failed",
        id: "runtime.connection.failed",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(trackError).toHaveBeenCalledWith({
        message: "Runtime connection failed",
        source: "chat",
        metadata: { msgId: "runtime.connection.failed" },
      });

      expect(store.dispatch).toHaveBeenCalledWith(expect.objectContaining({
        payload: message,
      }));
    });
  });

  describe("handleActionMessage", () => {
    it("should use first-person perspective for task completion messages", () => {
      // Test partial completion
      const messagePartial = {
        action: ActionType.FINISH,
        source: "agent",
        args: {
          final_thought: "",
          task_completed: "partial",
          outputs: {},
          thought: ""
        }
      };

      // Mock implementation to capture the message
      let capturedPartialMessage = "";
      store.dispatch.mockImplementation((action) => {
        if (action.type === "chat/addAssistantMessage" && 
            action.payload.includes("believe that the task was **completed partially**")) {
          capturedPartialMessage = action.payload;
        }
      });

      handleActionMessage(messagePartial);
      expect(capturedPartialMessage).toContain("I believe that the task was **completed partially**");
      
      // Test not completed
      const messageNotCompleted = {
        action: ActionType.FINISH,
        source: "agent",
        args: {
          final_thought: "",
          task_completed: "false",
          outputs: {},
          thought: ""
        }
      };

      // Mock implementation to capture the message
      let capturedNotCompletedMessage = "";
      store.dispatch.mockImplementation((action) => {
        if (action.type === "chat/addAssistantMessage" && 
            action.payload.includes("believe that the task was **not completed**")) {
          capturedNotCompletedMessage = action.payload;
        }
      });

      handleActionMessage(messageNotCompleted);
      expect(capturedNotCompletedMessage).toContain("I believe that the task was **not completed**");
      
      // Test completed successfully
      const messageCompleted = {
        action: ActionType.FINISH,
        source: "agent",
        args: {
          final_thought: "",
          task_completed: "true",
          outputs: {},
          thought: ""
        }
      };

      // Mock implementation to capture the message
      let capturedCompletedMessage = "";
      store.dispatch.mockImplementation((action) => {
        if (action.type === "chat/addAssistantMessage" && 
            action.payload.includes("believe that the task was **completed successfully**")) {
          capturedCompletedMessage = action.payload;
        }
      });

      handleActionMessage(messageCompleted);
      expect(capturedCompletedMessage).toContain("I believe that the task was **completed successfully**");
    });
  });
});
