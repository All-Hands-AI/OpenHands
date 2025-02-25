import {
  addAssistantMessage,
  addAssistantAction,
  addUserMessage,
  addErrorMessage,
} from "#/state/chat-slice";
import { trackError } from "#/utils/error-handler";
import { appendSecurityAnalyzerInput } from "#/state/security-analyzer-slice";
import { setCode, setActiveFilepath } from "#/state/code-slice";
import { appendJupyterInput } from "#/state/jupyter-slice";
import { setCurStatusMessage } from "#/state/status-slice";
import store from "#/store";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessage } from "./observations";
import { appendInput } from "#/state/command-slice";

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      store.dispatch(addAssistantMessage(message.message));
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      store.dispatch(addAssistantMessage(message.message));
    }
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(setActiveFilepath(path));
    store.dispatch(setCode(content));
  },
  [ActionType.MESSAGE]: (message: ActionMessage) => {
    if (message.source === "user") {
      store.dispatch(
        addUserMessage({
          content: message.args.content,
          imageUrls:
            typeof message.args.image_urls === "string"
              ? [message.args.image_urls]
              : message.args.image_urls,
          timestamp: message.timestamp,
          pending: false,
        }),
      );
    } else {
      store.dispatch(addAssistantMessage(message.args.content));
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      store.dispatch(appendJupyterInput(message.args.code));
    }
  },
};

function showLLMMetricsAlert(message: ActionMessage) {
  const metrics = message.llm_metrics;
  const usage = message.tool_call_metadata?.model_response?.usage;
  
  if (!metrics && !usage) return;
  
  const lines = ['LLM Information'];
  
  // Add metrics information (if available)
  if (metrics && metrics.accumulated_cost !== undefined) {
    lines.push(`Accumulated Cost: $${metrics.accumulated_cost.toFixed(4)}`);
  } else {
    lines.push('Accumulated Cost: Not available');
  }
  
  // Add usage information (regardless of whether metrics exists)
  if (usage) {
    lines.push(`Prompt Tokens: ${usage.prompt_tokens}`);
    lines.push(`Completion Tokens: ${usage.completion_tokens}`);
    lines.push(`Total Tokens: ${usage.total_tokens}`);
  } else {
    lines.push('Token Usage: Not available');
  }
  
  alert(lines.join('\n'));
}

export function handleActionMessage(message: ActionMessage) {
  // Print the message object
  console.log("Processing action message:", message);
  
  if (message.args?.hidden) {
    return;
  }

  // Handle LLM metrics display
  if (message.llm_metrics || message.tool_call_metadata?.model_response?.usage) {
    showLLMMetricsAlert(message);
  }

  if (message.action === ActionType.RUN) {
    store.dispatch(appendInput(message.args.command));
  }

  if ("args" in message && "security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message));
  }

  if (message.source === "agent") {
    if (message.args && message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
    // Need to convert ActionMessage to RejectAction
    // @ts-expect-error TODO: fix
    store.dispatch(addAssistantAction(message));
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleStatusMessage(message: StatusMessage) {
  if (message.type === "info") {
    store.dispatch(
      setCurStatusMessage({
        ...message,
      }),
    );
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
    store.dispatch(
      addErrorMessage({
        message: errorMsg,
      }),
    );
  }
}
