import { StatusMessage } from "#/types/message";
import { trackError } from "#/utils/error-handler";
import { addErrorMessage } from "#/state/chat-slice";
import store from "#/store";

// Global reference to the status update function
// This will be set by the StatusProvider when it mounts
let updateStatusMessageFn: ((message: StatusMessage) => void) | null = null;

/**
 * Register the status update function
 * This should be called by the StatusProvider when it mounts
 */
export function registerStatusService(
  updateFn: (message: StatusMessage) => void,
) {
  updateStatusMessageFn = updateFn;
}

/**
 * Handle a status message
 * This is used by the actions service
 */
export function handleStatusMessage(message: StatusMessage) {
  if (message.type === "info") {
    if (updateStatusMessageFn) {
      updateStatusMessageFn({
        ...message,
      });
    }
  } else if (message.type === "error") {
    trackError({
      message: message.message,
      source: "chat",
      metadata: { msgId: message.id },
    });
    store.dispatch(
      addErrorMessage({
        ...message,
      }),
    );
  }
}
