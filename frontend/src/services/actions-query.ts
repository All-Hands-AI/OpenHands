import { trackError } from "#/utils/error-handler";
import { appendSecurityAnalyzerInput } from "#/state/security-analyzer-slice";
import { setCode, setActiveFilepath } from "#/state/code-slice";
import { appendJupyterInput } from "#/state/jupyter-slice";
import store from "#/store";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessage } from "./observations-query";
import { handleStatusMessage } from "./status-service-query";
import { updateMetrics } from "./metrics-service-query";
import { appendInput } from "#/state/command-slice";
import { chatKeys } from "#/hooks/query/use-chat";

// Get the query client and chat functions
const getQueryClient = () =>
  // This is a workaround since we can't use hooks outside of components
  // In a real implementation, you might want to restructure this to use React context
  window.__queryClient;

// Helper function to get chat functions
const getChatFunctions = () => {
  const queryClient = getQueryClient();
  if (!queryClient) {
    console.error("Query client not available");
    return null;
  }

  // Create mutation functions
  const addUserMessage = (payload: {
    content: string;
    imageUrls: string[];
    timestamp: string;
    pending?: boolean;
  }) => {
    const currentState = queryClient.getQueryData(chatKeys.messages()) || {
      messages: [],
    };
    const newState = { ...currentState };

    const message = {
      type: "thought",
      sender: "user",
      content: payload.content,
      imageUrls: payload.imageUrls,
      timestamp: payload.timestamp || new Date().toISOString(),
      pending: !!payload.pending,
    };

    // Remove any pending messages
    let i = newState.messages.length;
    while (i) {
      i -= 1;
      const m = newState.messages[i];
      if (m.pending) {
        newState.messages.splice(i, 1);
      }
    }

    newState.messages.push(message);
    queryClient.setQueryData(chatKeys.messages(), newState);
  };

  const addAssistantMessage = (content: string) => {
    const currentState = queryClient.getQueryData(chatKeys.messages()) || {
      messages: [],
    };
    const newState = { ...currentState };

    const message = {
      type: "thought",
      sender: "assistant",
      content,
      imageUrls: [],
      timestamp: new Date().toISOString(),
      pending: false,
    };

    newState.messages.push(message);
    queryClient.setQueryData(chatKeys.messages(), newState);
  };

  const addAssistantAction = (action: Record<string, unknown>) => {
    const currentState = queryClient.getQueryData(chatKeys.messages()) || {
      messages: [],
    };
    const newState = { ...currentState };

    // Implementation similar to the one in use-chat.ts
    // This is simplified for brevity
    const message = {
      type: "action",
      sender: "assistant",
      translationID: `ACTION_MESSAGE$${action.action.toUpperCase()}`,
      eventID: action.id,
      content: action.args?.thought || action.message || "",
      imageUrls: [],
      timestamp: new Date().toISOString(),
    };

    newState.messages.push(message);
    queryClient.setQueryData(chatKeys.messages(), newState);
  };

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
    addUserMessage,
    addAssistantMessage,
    addAssistantAction,
    addErrorMessage,
  };
};

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      const chatFunctions = getChatFunctions();
      if (chatFunctions) {
        chatFunctions.addAssistantMessage(message.message);
      }
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      const chatFunctions = getChatFunctions();
      if (chatFunctions) {
        chatFunctions.addAssistantMessage(message.message);
      }
    }
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(setActiveFilepath(path));
    store.dispatch(setCode(content));
  },
  [ActionType.MESSAGE]: (message: ActionMessage) => {
    const chatFunctions = getChatFunctions();
    if (!chatFunctions) return;

    if (message.source === "user") {
      chatFunctions.addUserMessage({
        content: message.args.content,
        imageUrls:
          typeof message.args.image_urls === "string"
            ? [message.args.image_urls]
            : message.args.image_urls,
        timestamp: message.timestamp,
        pending: false,
      });
    } else {
      chatFunctions.addAssistantMessage(message.args.content);
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      store.dispatch(appendJupyterInput(message.args.code));
    }
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    const chatFunctions = getChatFunctions();
    if (!chatFunctions) return;

    chatFunctions.addAssistantMessage(message.args.final_thought);
    let successPrediction = "";
    if (message.args.task_completed === "partial") {
      successPrediction =
        "I believe that the task was **completed partially**.";
    } else if (message.args.task_completed === "false") {
      successPrediction = "I believe that the task was **not completed**.";
    } else if (message.args.task_completed === "true") {
      successPrediction =
        "I believe that the task was **completed successfully**.";
    }
    if (successPrediction) {
      // if final_thought is not empty, add a new line before the success prediction
      if (message.args.final_thought) {
        chatFunctions.addAssistantMessage(`\n${successPrediction}`);
      } else {
        chatFunctions.addAssistantMessage(successPrediction);
      }
    }
  },
};

export function handleActionMessage(message: ActionMessage) {
  if (message.args?.hidden) {
    return;
  }

  // Update metrics if available
  if (
    message.llm_metrics ||
    message.tool_call_metadata?.model_response?.usage
  ) {
    const metrics = {
      cost: message.llm_metrics?.accumulated_cost ?? null,
      usage: message.tool_call_metadata?.model_response?.usage ?? null,
    };
    updateMetrics(metrics);
  }

  if (message.action === ActionType.RUN) {
    store.dispatch(appendInput(message.args.command));
  }

  if ("args" in message && "security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message));
  }

  if (message.source === "agent") {
    const chatFunctions = getChatFunctions();
    if (!chatFunctions) return;

    if (message.args && message.args.thought) {
      chatFunctions.addAssistantMessage(message.args.thought);
    }
    // Need to convert ActionMessage to RejectAction
    chatFunctions.addAssistantAction(message);
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleAssistantMessage(message: Record<string, unknown>) {
  if (message.action) {
    handleActionMessage(message as unknown as ActionMessage);
  } else if (message.observation) {
    handleObservationMessage(message as unknown as ObservationMessage);
  } else if (message.status_update) {
    handleStatusMessage(message as unknown as StatusMessage);
  } else {
    const errorMsg = "Unknown message type received";
    trackError({
      message: errorMsg,
      source: "chat",
      metadata: { raw_message: message },
    });

    const chatFunctions = getChatFunctions();
    if (chatFunctions) {
      chatFunctions.addErrorMessage({
        message: errorMsg,
      });
    }
  }
}
