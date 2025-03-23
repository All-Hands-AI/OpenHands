import { trackError } from "#/services/context-services/metrics-service";
import { addErrorMessage } from "#/services/context-services/chat-service";

// Function types
type UpdateStatusFn = (message: {
  id: string;
  message: string;
  type: "info" | "error" | "warning" | "success";
}) => void;

// Module-level variables to store the actual functions
let updateStatusImpl: UpdateStatusFn = () => {};

// Register the functions from the context
export function registerStatusFunctions({
  updateStatus,
}: {
  updateStatus: UpdateStatusFn;
}): void {
  updateStatusImpl = updateStatus;
}

// For backward compatibility
export function registerStatusService(updateStatus: UpdateStatusFn): void {
  updateStatusImpl = updateStatus;
}

// Export the service functions
export const StatusService = {
  updateStatus: (message: {
    id: string;
    message: string;
    type: "info" | "error" | "warning" | "success";
  }): void => {
    updateStatusImpl(message);

    // If it's an error, also track it and add it to the chat
    if (message.type === "error") {
      trackError({
        message: message.message,
        source: "chat",
        metadata: { msgId: message.id },
      });
      addErrorMessage({
        ...message,
      });
    }
  },
};

// Re-export the service functions for convenience
export const { updateStatus } = StatusService;
