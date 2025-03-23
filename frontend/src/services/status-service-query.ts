import { StatusMessage } from "#/types/message";
import { statusKeys } from "#/hooks/query/use-status";
import { chatKeys } from "#/hooks/query/use-chat";
import { trackError } from "#/utils/error-handler";

// Get the query client
const getQueryClient = () =>
  // This is a workaround since we can't use hooks outside of components
  // In a real implementation, you might want to restructure this to use React context
  window.__queryClient;

// Helper function to get status functions
const getStatusFunctions = () => {
  const queryClient = getQueryClient();
  if (!queryClient) {
    console.error("Query client not available");
    return null;
  }

  const setStatusMessage = (newStatusMessage: StatusMessage) => {
    queryClient.setQueryData(statusKeys.current(), newStatusMessage);
  };

  return {
    setStatusMessage,
  };
};

// Helper function to get chat functions
const getChatFunctions = () => {
  const queryClient = getQueryClient();
  if (!queryClient) {
    console.error("Query client not available");
    return null;
  }

  const addErrorMessage = (payload: { id?: string; message: string }) => {
    const currentState = queryClient.getQueryData(chatKeys.messages()) || {
      messages: [],
    };
    const newState = { ...currentState };

    const { id, message } = payload;
    newState.messages.push({
      translationID: id,
      content: message,
      type: "error",
      sender: "assistant",
      timestamp: new Date().toISOString(),
    });

    queryClient.setQueryData(chatKeys.messages(), newState);
  };

  return {
    addErrorMessage,
  };
};

export function handleStatusMessage(message: StatusMessage) {
  const statusFunctions = getStatusFunctions();
  if (!statusFunctions) return;

  statusFunctions.setStatusMessage(message);

  if (message.type === "error") {
    // Track the error for analytics
    trackError({
      message: message.message,
      source: "chat",
      metadata: { msgId: message.id },
    });
    
    const chatFunctions = getChatFunctions();
    if (chatFunctions) {
      chatFunctions.addErrorMessage({
        id: message.id,
        message: message.message,
      });
    }
  }
}
