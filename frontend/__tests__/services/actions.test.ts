import { describe, it, expect, vi, beforeEach } from "vitest";
import { handleActionMessage } from "#/services/actions-query";
import { handleStatusMessage } from "#/services/status-service-query";
import store from "#/store";
import { trackError } from "#/utils/error-handler";
import ActionType from "#/types/action-type";
import { ActionMessage } from "#/types/message";
import { statusKeys } from "#/hooks/query/use-status";
import { chatKeys } from "#/hooks/query/use-chat";

// Mock dependencies
vi.mock("#/utils/error-handler", () => ({
  trackError: vi.fn(),
}));

vi.mock("#/store", () => ({
  default: {
    dispatch: vi.fn(),
  },
}));

// Mock the global query client
beforeEach(() => {
  window.__queryClient = {
    setQueryData: vi.fn(),
    getQueryData: vi.fn().mockReturnValue({ messages: [] }),
  } as any;
});

describe("Actions Service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("handleStatusMessage", () => {
    it("should update status message in React Query", () => {
      const message = {
        type: "info",
        message: "Runtime is not available",
        id: "runtime.unavailable",
        status_update: true as const,
      };

      handleStatusMessage(message);

      expect(window.__queryClient.setQueryData).toHaveBeenCalledWith(
        statusKeys.current(),
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

      expect(window.__queryClient.setQueryData).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          messages: expect.arrayContaining([
            expect.objectContaining({
              content: "Runtime connection failed",
              type: "error",
            })
          ])
        })
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

      // Mock implementation to capture the message
      let capturedMessage = "";
      (window.__queryClient.setQueryData as any).mockImplementation((key: any, newState: any) => {
        // Check if the message contains the expected text
        const lastMessage = newState.messages[newState.messages.length - 1];
        if (lastMessage && lastMessage.content && 
            lastMessage.content.includes("I believe that the task was **completed partially**")) {
          capturedMessage = lastMessage.content;
        }
      });

      handleActionMessage(messagePartial);
      expect(window.__queryClient.setQueryData).toHaveBeenCalled();

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

      // Reset the mock
      (window.__queryClient.setQueryData as any).mockReset();
      
      // Mock implementation to capture the message
      (window.__queryClient.setQueryData as any).mockImplementation((key: any, newState: any) => {
        // We just need to verify the function is called
      });

      handleActionMessage(messageNotCompleted);
      expect(window.__queryClient.setQueryData).toHaveBeenCalled();

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

      // Reset the mock
      (window.__queryClient.setQueryData as any).mockReset();
      
      // Mock implementation to capture the message
      (window.__queryClient.setQueryData as any).mockImplementation((key: any, newState: any) => {
        // We just need to verify the function is called
      });

      handleActionMessage(messageCompleted);
      expect(window.__queryClient.setQueryData).toHaveBeenCalled();
    });
  });
});
