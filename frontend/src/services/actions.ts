import { trackError } from "#/utils/error-handler";
import { appendSecurityAnalyzerInput } from "#/state/security-analyzer-slice";
import { setCode, setActiveFilepath } from "#/state/code-slice";
import { appendJupyterInput } from "#/state/jupyter-slice";
import { setMetrics } from "#/state/metrics-slice";
import store from "#/store";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessage } from "./observations";
import { appendInput } from "#/state/command-slice";
import { queryClient } from "#/entry.client";
import {
  addAssistantMessage as addAssistantMessageToChat,
  addErrorMessage as addErrorMessageToChat,
} from "#/hooks/query/use-chat-messages";

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    console.log("BROWSE action received:", message);
    if (!message.args.thought && message.message) {
      console.log("Adding BROWSE message to chat:", message.message);
      addAssistantMessageToChat(queryClient, message.message);
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    console.log("BROWSE_INTERACTIVE action received:", message);
    if (!message.args.thought && message.message) {
      console.log("Adding BROWSE_INTERACTIVE message to chat:", message.message);
      addAssistantMessageToChat(queryClient, message.message);
    }
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(setActiveFilepath(path));
    store.dispatch(setCode(content));
  },
  [ActionType.MESSAGE]: (message: ActionMessage) => {
    console.log("MESSAGE action received in actions.ts - SKIPPING to avoid duplicates");
    // Messages are now handled directly in the ws-client-provider
    // This prevents duplicate messages
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      store.dispatch(appendJupyterInput(message.args.code));
    }
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    console.log("FINISH action received:", message);
    console.log("Adding final thought to chat:", message.args.final_thought);
    addAssistantMessageToChat(queryClient, message.args.final_thought);
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
        console.log("Adding success prediction with newline:", successPrediction);
        addAssistantMessageToChat(queryClient, `\n${successPrediction}`);
      } else {
        console.log("Adding success prediction:", successPrediction);
        addAssistantMessageToChat(queryClient, successPrediction);
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
    store.dispatch(setMetrics(metrics));
  }

  if (message.action === ActionType.RUN) {
    store.dispatch(appendInput(message.args.command));
  }

  if ("args" in message && "security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message));
  }

  if (message.source === "agent") {
    if (message.args && message.args.thought) {
      addAssistantMessageToChat(queryClient, message.args.thought);
    }
    // TODO: Handle action messages in React Query
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleStatusMessage(message: StatusMessage) {
  if (message.type === "error") {
    trackError({
      message: message.message,
      source: "chat",
      metadata: { msgId: message.id },
    });
    addErrorMessageToChat(queryClient, {
      ...message,
    });
  }
}

export function handleAssistantMessage(message: Record<string, unknown>) {
  console.log("handleAssistantMessage received:", message);
  
  if (message.action) {
    console.log("Processing action message:", message.action);
    handleActionMessage(message as unknown as ActionMessage);
  } else if (message.observation) {
    console.log("Processing observation message:", message.observation);
    handleObservationMessage(message as unknown as ObservationMessage);
  } else if (message.status_update) {
    console.log("Processing status message:", message.status_update);
    handleStatusMessage(message as unknown as StatusMessage);
  } else {
    console.log("Unknown message type received:", message);
    const errorMsg = "Unknown message type received";
    trackError({
      message: errorMsg,
      source: "chat",
      metadata: { raw_message: message },
    });
    addErrorMessageToChat(queryClient, {
      message: errorMsg,
    });
  }
}
