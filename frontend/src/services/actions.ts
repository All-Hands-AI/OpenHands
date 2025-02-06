import {
  addAssistantMessage,
  addAssistantAction,
  addUserMessage,
  addErrorMessage,
} from "#/state/chat-slice";
import {
  appendSecurityAnalyzerInput,
  ActionSecurityRisk,
} from "#/state/security-analyzer-slice";
import { setCode, setActiveFilepath } from "#/state/code-slice";
import { appendJupyterInput } from "#/state/jupyter-slice";
import { setCurStatusMessage } from "#/state/status-slice";
import store from "#/store";

import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { OpenHandsEventType } from "#/types/core/base";

import { handleObservationMessage } from "./observations";
import { appendInput } from "#/state/command-slice";

const messageActions = {
  browse: (message: ActionMessage) => {
    if (!message.args.thought && message.args.message) {
      store.dispatch(addAssistantMessage(message.args.message as string));
    }
  },
  browse_interactive: (message: ActionMessage) => {
    if (!message.args.thought && message.args.message) {
      store.dispatch(addAssistantMessage(message.args.message as string));
    }
  },
  write: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(setActiveFilepath(path));
    store.dispatch(setCode(content));
  },
  message: (message: ActionMessage) => {
    if (message.args.source === "user") {
      store.dispatch(
        addUserMessage({
          content: message.args.content as string,
          imageUrls:
            typeof message.args.image_urls === "string"
              ? [message.args.image_urls as string]
              : (message.args.image_urls as string[]),
          timestamp: message.timestamp,
          pending: false,
        }),
      );
    } else {
      store.dispatch(addAssistantMessage(message.args.content as string));
    }
  },
  run_ipython: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      store.dispatch(appendJupyterInput(message.args.code));
    }
  },
};

export function handleActionMessage(message: ActionMessage) {
  if (message.args?.hidden) {
    return;
  }

  if (message.args.action === "run") {
    store.dispatch(appendInput(message.args.command as string));
  }

  if ("security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message));
  }

  if (message.args.source === "agent") {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought as string));
    }
    const actionType = message.args.action as OpenHandsEventType;
    const basePayload = {
      source: "agent" as const,
      id: parseInt(message.eventID || "0", 10),
      message: (message.args.message as string) || "",
      timestamp: new Date().toISOString(),
    };

    switch (actionType) {
      case "reject":
        store.dispatch(
          addAssistantAction({
            ...basePayload,
            action: "reject",
            args: { thought: (message.args.thought as string) || "" },
          }),
        );
        break;
      case "message":
        store.dispatch(
          addAssistantAction({
            ...basePayload,
            action: "message",
            args: {
              thought: (message.args.thought as string) || "",
              image_urls: [],
              wait_for_response: false,
            },
          }),
        );
        break;
      case "run":
        store.dispatch(
          addAssistantAction({
            ...basePayload,
            action: "run",
            args: {
              command: (message.args.command as string) || "",
              security_risk:
                (message.args.security_risk as ActionSecurityRisk) ||
                ActionSecurityRisk.UNKNOWN,
              confirmation_state: "awaiting_confirmation",
              thought: (message.args.thought as string) || "",
            },
          }),
        );
        break;
      default:
        // For other action types, we'll need to handle them specifically
        // For now, we'll skip dispatching if the action type isn't handled
        break;
    }
  }

  const actionType = message.args.action as keyof typeof messageActions;
  if (actionType in messageActions) {
    const actionFn = messageActions[actionType];
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
        id: message.id,
        message: message.message || message.content || "Unknown error",
        content: message.message || message.content || "Unknown error",
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
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
    store.dispatch(
      addErrorMessage({
        message: "Unknown message type received",
        content: "Unknown message type received",
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      }),
    );
  }
}
