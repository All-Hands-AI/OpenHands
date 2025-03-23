import { StatusMessage } from "#/types/message";
import { trackError } from "#/utils/error-handler";
import { queryClient } from "#/entry.client";
import { statusKeys } from "#/hooks/query/use-status";
import { chatKeys } from "#/hooks/query/use-chat";

export function handleStatusMessage(message: StatusMessage) {
  if (message.type === "info") {
    // Update the status message using React Query
    queryClient.setQueryData(statusKeys.current(), message);
  } else if (message.type === "error") {
    trackError({
      message: message.message,
      source: "chat",
      metadata: { msgId: message.id },
    });

    // Get current chat state
    const currentState = queryClient.getQueryData(chatKeys.messages()) || {
      messages: [],
    };
    const newState = { ...currentState };

    // Add error message
    newState.messages.push({
      translationID: message.id,
      content: message.message,
      type: "error",
      sender: "assistant",
      timestamp: new Date().toISOString(),
    });

    // Update chat state
    queryClient.setQueryData(chatKeys.messages(), newState);
  }
}
