import {
  addAssistantMessage,
  addAssistantAction,
  addUserMessage,
  addErrorMessage,
} from "#/state/chat-slice";
import { setCode, setActiveFilepath } from "#/state/code-slice";
import { appendJupyterInput } from "#/state/jupyter-slice";
import {
  ActionSecurityRisk,
  appendSecurityAnalyzerInput,
} from "#/state/security-analyzer-slice";
import { setCurStatusMessage } from "#/state/status-slice";
import store from "#/store";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import EventLogger from "#/utils/event-logger";
import { handleObservationMessage } from "./observations";

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    } else {
      store.dispatch(addAssistantMessage(message.message));
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    } else {
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
          imageUrls: [],
          timestamp: message.timestamp,
          pending: false,
        }),
      );
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      store.dispatch(appendJupyterInput(message.args.code));
    }
  },
};

function getRiskText(risk: ActionSecurityRisk) {
  switch (risk) {
    case ActionSecurityRisk.LOW:
      return "Low Risk";
    case ActionSecurityRisk.MEDIUM:
      return "Medium Risk";
    case ActionSecurityRisk.HIGH:
      return "High Risk";
    case ActionSecurityRisk.UNKNOWN:
    default:
      return "Unknown Risk";
  }
}

export function handleActionMessage(message: ActionMessage) {
  if ("args" in message && "security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message));
  }

  if (
    (message.action === ActionType.RUN ||
      message.action === ActionType.RUN_IPYTHON) &&
    message.args.confirmation_state === "awaiting_confirmation"
  ) {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
    if (message.args.command) {
      store.dispatch(
        addAssistantMessage(
          `Running this command now: \n\`\`\`\`bash\n${message.args.command}\n\`\`\`\`\nEstimated security risk: ${getRiskText(message.args.security_risk as unknown as ActionSecurityRisk)}`,
        ),
      );
    } else if (message.args.code) {
      store.dispatch(
        addAssistantMessage(
          `Running this code now: \n\`\`\`\`python\n${message.args.code}\n\`\`\`\`\nEstimated security risk: ${getRiskText(message.args.security_risk as unknown as ActionSecurityRisk)}`,
        ),
      );
    } else {
      store.dispatch(addAssistantMessage(message.message));
    }
    return;
  }

  if (message.source !== "user" && !message.args?.hidden) {
    if (message.args && message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
    // Convert the message to a properly typed action
    const baseAction = {
      ...message,
      source: "agent" as const,
      args: {
        ...message.args,
        thought: message.args?.thought || message.message || "",
      },
    };

    // Cast to the appropriate action type based on the action field
    switch (message.action) {
      case "run":
        store.dispatch(
          addAssistantAction({
            ...baseAction,
            action: "run" as const,
            args: {
              command: String(message.args?.command || ""),
              confirmation_state: (message.args?.confirmation_state ||
                "confirmed") as
                | "confirmed"
                | "rejected"
                | "awaiting_confirmation",
              thought: String(message.args?.thought || message.message || ""),
              hidden: Boolean(message.args?.hidden),
            },
          }),
        );
        break;
      case "message":
        store.dispatch(
          addAssistantAction({
            ...baseAction,
            action: "message" as const,
            args: {
              content: String(message.args?.content || message.message || ""),
              image_urls: Array.isArray(message.args?.image_urls)
                ? message.args.image_urls
                : null,
              wait_for_response: Boolean(message.args?.wait_for_response),
            },
          }),
        );
        break;
      case "run_ipython":
        store.dispatch(
          addAssistantAction({
            ...baseAction,
            action: "run_ipython" as const,
            args: {
              code: String(message.args?.code || ""),
              confirmation_state: (message.args?.confirmation_state ||
                "confirmed") as
                | "confirmed"
                | "rejected"
                | "awaiting_confirmation",
              kernel_init_code: String(message.args?.kernel_init_code || ""),
              thought: String(message.args?.thought || message.message || ""),
            },
          }),
        );
        break;
      default:
        // For other action types, ensure we have the required thought property
        store.dispatch(
          addAssistantAction({
            ...baseAction,
            action: "reject" as const,
            args: {
              thought: String(message.args?.thought || message.message || ""),
            },
          }),
        );
    }
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
    EventLogger.error(`Unknown message type ${message}`);
  }
}
