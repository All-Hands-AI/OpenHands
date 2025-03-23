import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleStatusMessage, handleActionMessage } from "#/services/actions";
import { trackError } from "#/utils/error-handler";
import { updateStatus } from "#/services/context-services/status-service";
import { addAssistantMessage } from "#/services/context-services/chat-service";
import ActionType from "#/types/action-type";
import { ActionMessage } from "#/types/message";

// Mock dependencies
vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

vi.mock("#/services/context-services/status-service", () => ({
  updateStatus: vi.fn(),
}));

vi.mock("#/services/context-services/chat-service", () => ({
  addAssistantMessage: vi.fn(),
  addErrorMessage: vi.fn(),
}));

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
    it("should update status with info messages", () => {
      const message = {
        type: "info" as const,
        message: "Runtime is not available",
        id: "runtime.unavailable",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(updateStatus).toHaveBeenCalledWith({
        id: "runtime.unavailable",
        message: "Runtime is not available",
        type: "info",
      });
    });

    it("should log error messages and update status", () => {
      const message = {
        type: "error" as const,
        message: "Runtime connection failed",
        id: "runtime.connection.failed",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(updateStatus).toHaveBeenCalledWith({
        id: "runtime.connection.failed",
        message: "Runtime connection failed",
        type: "error",
      });
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
        type: ActionType.TASK_COMPLETION,
        args: {
          final_thought: "",
          task_completed: "partial",
          outputs: "",
          thought: ""
        }
      };

      handleActionMessage(messagePartial);
      
      expect(addAssistantMessage).toHaveBeenCalledWith(
        expect.stringContaining("I believe that the task was **completed partially**")
      );

      // Test not completed
      const messageNotCompleted: ActionMessage = {
        id: 2,
        action: ActionType.FINISH,
        source: "agent",
        message: "",
        timestamp: new Date().toISOString(),
        type: ActionType.TASK_COMPLETION,
        args: {
          final_thought: "",
          task_completed: "false",
          outputs: "",
          thought: ""
        }
      };

      handleActionMessage(messageNotCompleted);
      
      expect(addAssistantMessage).toHaveBeenCalledWith(
        expect.stringContaining("I believe that the task was **not completed successfully**")
      );

      // Test completed successfully
      const messageCompleted: ActionMessage = {
        id: 3,
        action: ActionType.FINISH,
        source: "agent",
        message: "",
        timestamp: new Date().toISOString(),
        type: ActionType.TASK_COMPLETION,
        args: {
          final_thought: "",
          task_completed: "true",
          outputs: "",
          thought: ""
        }
      };

      handleActionMessage(messageCompleted);
      
      expect(addAssistantMessage).toHaveBeenCalledWith(
        expect.stringContaining("I believe that the task was **completed successfully**")
      );
    });
  });
});
