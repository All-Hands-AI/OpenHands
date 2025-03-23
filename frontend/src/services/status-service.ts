import { StatusMessage } from "#/types/message";
import { trackError } from "#/utils/error-handler";
import { queryClient } from "#/entry.client";
import { statusKeys } from "#/hooks/query/use-status";
import { addErrorMessage } from "#/state/chat-slice";
import store from "#/store";

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
    store.dispatch(
      addErrorMessage({
        ...message,
      }),
    );
  }
}
