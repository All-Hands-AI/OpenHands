import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleStatusMessage, handleActionMessage } from "#/services/actions";
// store import removed
import { trackError } from "#/utils/error-handler";
import ActionType from "#/types/action-type";
import { ActionMessage } from "#/types/message";
// queryReduxBridge import removed
import * as observations from "#/services/observations";

// Mock dependencies
vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

// Mock QueryReduxBridge
vi.mock("#/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: vi.fn(() => ({
    isSliceMigrated: vi.fn(() => true),
    syncReduxToQuery: vi.fn(),
    conditionalDispatch: vi.fn(),
  })),
}));

// Create a mock for the chat functions
const mockAddErrorMessage = vi.fn();
const mockAddAssistantMessage = vi.fn();

// Mock the getChatFunctions method
vi.spyOn(observations, "getChatFunctions").mockImplementation(() => ({
  addErrorMessage: mockAddErrorMessage,
  addAssistantMessage: mockAddAssistantMessage,
  addAssistantAction: vi.fn(),
  addAssistantObservation: vi.fn(),
  addUserMessage: vi.fn(),
  clearMessages: vi.fn(),
  messages: [],
  isLoading: false,
}));

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
    it("should handle info messages without dispatching to Redux (now using React Query)", () => {
      const message = {
        type: "info",
        message: "Runtime is not available",
        id: "runtime.unavailable",
        status_update: true as const,
      };

      handleStatusMessage(message);

      // We no longer dispatch to Redux for info messages
      expect(store.dispatch).not.toHaveBeenCalled();
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

      // Now we should check if the React Query function was called instead of Redux
      expect(mockAddErrorMessage).toHaveBeenCalledWith(message);
    });
  });

  describe("handleActionMessage", () => {
    it("should update metrics via React Query when metrics are available", () => {
      const message: ActionMessage = {
        id: 1,
        action: ActionType.MESSAGE,
        source: "agent",
        message: "Test message",
        timestamp: new Date().toISOString(),
        args: {
          content: "Test content",
        },
        llm_metrics: {
          accumulated_cost: 0.05,
        },
        tool_call_metadata: {
          model_response: {
            usage: {
              prompt_tokens: 100,
              completion_tokens: 50,
              total_tokens: 150,
            }
          }
        }
      };

      const mockBridge = {
        isSliceMigrated: vi.fn(() => true),
        syncReduxToQuery: vi.fn(),
        conditionalDispatch: vi.fn(),
      };
      
      vi.mocked(queryReduxBridge.getQueryReduxBridge).mockReturnValue(mockBridge as any);

      handleActionMessage(message);

      expect(mockBridge.isSliceMigrated).toHaveBeenCalledWith("metrics");
      expect(mockBridge.syncReduxToQuery).toHaveBeenCalledWith(
        ["metrics"],
        {
          cost: 0.05,
          usage: {
            prompt_tokens: 100,
            completion_tokens: 50,
            total_tokens: 150,
          }
        }
      );
    });

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

      // Reset the mock before testing
      mockAddAssistantMessage.mockReset();

      handleActionMessage(messagePartial);
      
      // Check if the addAssistantMessage was called with the right message
      expect(mockAddAssistantMessage).toHaveBeenCalledWith(
        expect.stringContaining("I believe that the task was **completed partially**")
      );

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

      // Reset the mock before testing
      mockAddAssistantMessage.mockReset();

      handleActionMessage(messageNotCompleted);
      
      // Check if the addAssistantMessage was called with the right message
      expect(mockAddAssistantMessage).toHaveBeenCalledWith(
        expect.stringContaining("I believe that the task was **not completed**")
      );

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

      // Reset the mock before testing
      mockAddAssistantMessage.mockReset();

      handleActionMessage(messageCompleted);
      
      // Check if the addAssistantMessage was called with the right message
      expect(mockAddAssistantMessage).toHaveBeenCalledWith(
        expect.stringContaining("I believe that the task was **completed successfully**")
      );
    });
  });
});
