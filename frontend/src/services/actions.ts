import {
  addAssistantMessage,
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
        }),
      );
    } else {
      store.dispatch(addAssistantMessage(message.args.content));
    }
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    store.dispatch(addAssistantMessage(message.message));
  },
  [ActionType.REJECT]: (message: ActionMessage) => {
    store.dispatch(addAssistantMessage(message.message));
  },
  [ActionType.DELEGATE]: (message: ActionMessage) => {
    store.dispatch(addAssistantMessage(message.message));
  },
  [ActionType.RUN]: (message: ActionMessage) => {
    if (message.args.hidden) return;
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
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
    console.error("Unknown message type", message);
  }
}
