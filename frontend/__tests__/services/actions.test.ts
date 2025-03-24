import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleStatusMessage, handleActionMessage } from "#/services/actions";
import store from "#/store";
import { trackError } from "#/utils/error-handler";
import ActionType from "#/types/action-type";
import { ActionMessage } from "#/types/message";
import { setAgentStatus } from "#/hooks/query/use-agent-status";

// Mock dependencies
vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

vi.mock("#/hooks/query/use-agent-status", () => ({
  setAgentStatus: vi.fn(),
}));

// Mock dynamic import
vi.mock("#/entry.client", () => ({
  queryClient: {
    setQueryData: vi.fn(),
  },
}));

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
    it("should set info messages in the query cache", async () => {
      const message = {
        type: "info",
        message: "Runtime is not available",
        id: "runtime.unavailable",
        status_update: true as const,
      };

      handleStatusMessage(message);
      
      // Wait for the dynamic import promise to resolve
      await new Promise(resolve => setTimeout(resolve, 0));
      
      // Verify setAgentStatus was called with the message
      expect(setAgentStatus).toHaveBeenCalledWith(
        expect.anything(),
        message
      );
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
      const messagePartial: ActionMessage = {
        id: 1,
        action: ActionType.FINISH,
        source: "agent",
        message: "",
        timestamp: new Date().toISOString(),
        args: {
          final_thought: "",
          task_completed: "partial",
          outputs: "",
          thought: ""
        }
      };

      // Mock implementation to capture the message
      let capturedPartialMessage = "";
      (store.dispatch as any).mockImplementation((action: any) => {
        if (action.type === "chat/addAssistantMessage" &&
            action.payload.includes("believe that the task was **completed partially**")) {
          capturedPartialMessage = action.payload;
        }
      });

      handleActionMessage(messagePartial);
      expect(capturedPartialMessage).toContain("I believe that the task was **completed partially**");

      // Test not completed
      const messageNotCompleted: ActionMessage = {
        id: 2,
        action: ActionType.FINISH,
        source: "agent",
        message: "",
        timestamp: new Date().toISOString(),
        args: {
          final_thought: "",
          task_completed: "false",
          outputs: "",
          thought: ""
        }
      };

      // Mock implementation to capture the message
      let capturedNotCompletedMessage = "";
      (store.dispatch as any).mockImplementation((action: any) => {
        if (action.type === "chat/addAssistantMessage" &&
            action.payload.includes("believe that the task was **not completed**")) {
          capturedNotCompletedMessage = action.payload;
        }
      });

      handleActionMessage(messageNotCompleted);
      expect(capturedNotCompletedMessage).toContain("I believe that the task was **not completed**");

      // Test completed successfully
      const messageCompleted: ActionMessage = {
        id: 3,
        action: ActionType.FINISH,
        source: "agent",
        message: "",
        timestamp: new Date().toISOString(),
        args: {
          final_thought: "",
          task_completed: "true",
          outputs: "",
          thought: ""
        }
      };

      // Mock implementation to capture the message
      let capturedCompletedMessage = "";
      (store.dispatch as any).mockImplementation((action: any) => {
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
