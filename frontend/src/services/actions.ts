import { addAssistantMessage } from "#/state/chatSlice";
import { setCode, setActiveFilepath } from "#/state/codeSlice";
import {
  ActionSecurityRisk,
  appendSecurityAnalyzerInput,
} from "#/state/securityAnalyzerSlice";
import store from "#/store";
import ActionType from "#/types/ActionType";
import { ActionMessage } from "#/types/Message";

const messageActions = {
  [ActionType.BROWSE]: () => {
    // now handled by the Session context
  },
  [ActionType.BROWSE_INTERACTIVE]: () => {
    // now handled by the Session context
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(setActiveFilepath(path));
    store.dispatch(setCode(content));
  },
  [ActionType.MESSAGE]: () => {
    // now handled by the Session context
  },
  [ActionType.FINISH]: () => {
    // now handled by the Session context
  },
  [ActionType.REJECT]: () => {
    // now handled by the Session context
  },
  [ActionType.DELEGATE]: () => {
    // now handled by the Session context
  },
  [ActionType.RUN]: () => {
    // now handled by the Session context
  },
  [ActionType.RUN_IPYTHON]: () => {
    // now handled by the Session context
  },
  [ActionType.ADD_TASK]: () => {
    // now handled by the Session context
  },
  [ActionType.MODIFY_TASK]: () => {
    // now handled by the Session context
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
    message.args.is_confirmed === "awaiting_confirmation"
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

export function handleAssistantMessage(data: string) {
  const socketMessage = JSON.parse(data);

  if ("action" in socketMessage) {
    handleActionMessage(socketMessage);
  }
}
