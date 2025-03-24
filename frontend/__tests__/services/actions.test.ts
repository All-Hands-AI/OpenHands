import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleStatusMessage, handleActionMessage } from "#/services/actions";
import store from "#/store";
import { trackError } from "#/utils/error-handler";
import ActionType from "#/types/action-type";
import { ActionMessage } from "#/types/message";
import { setAgentStatus } from "#/hooks/query/use-agent-status";
import { addAssistantMessage, addErrorMessage } from "#/hooks/query/use-chat-messages";

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

vi.mock("#/hooks/query/use-chat-messages", () => ({
  addAssistantMessage: vi.fn(),
  addErrorMessage: vi.fn(),
}));

// Mock dynamic import
vi.mock("#/entry.client", () => ({
  queryClient: {
    getQueryData: vi.fn(),
    setQueryData: vi.fn(),
  },
}));

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
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

      expect(addErrorMessage).toHaveBeenCalledWith(
        expect.anything(),
        message
      );
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

      handleActionMessage(messagePartial);
      
      // Check that addAssistantMessage was called with the right message
      expect(addAssistantMessage).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining("I believe that the task was **completed partially**")
      );

      vi.clearAllMocks();

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

      handleActionMessage(messageNotCompleted);
      
      // Check that addAssistantMessage was called with the right message
      expect(addAssistantMessage).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining("I believe that the task was **not completed**")
      );

      vi.clearAllMocks();

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

      handleActionMessage(messageCompleted);
      
      // Check that addAssistantMessage was called with the right message
      expect(addAssistantMessage).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining("I believe that the task was **completed successfully**")
      );
    });
  });
});
