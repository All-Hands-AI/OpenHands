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
import { setMetrics } from "#/state/metrics-slice";
import store from "#/store";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessageWithBridge } from "./observations-with-bridge";
import { appendInput } from "#/state/command-slice";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      const bridge = getQueryReduxBridge();
      bridge.conditionalDispatch("chat", addAssistantMessage(message.message));
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      const bridge = getQueryReduxBridge();
      bridge.conditionalDispatch("chat", addAssistantMessage(message.message));
    }
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    const bridge = getQueryReduxBridge();
    bridge.conditionalDispatch("code", setActiveFilepath(path));
    bridge.conditionalDispatch("code", setCode(content));
  },
  [ActionType.MESSAGE]: (message: ActionMessage) => {
    const bridge = getQueryReduxBridge();
    if (message.source === "user") {
      bridge.conditionalDispatch(
        "chat",
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
      bridge.conditionalDispatch("chat", addAssistantMessage(message.args.content));
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      const bridge = getQueryReduxBridge();
      bridge.conditionalDispatch("jupyter", appendJupyterInput(message.args.code));
    }
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    const bridge = getQueryReduxBridge();
    bridge.conditionalDispatch("chat", addAssistantMessage(message.args.final_thought));
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
        bridge.conditionalDispatch("chat", addAssistantMessage(`\n${successPrediction}`));
      } else {
        bridge.conditionalDispatch("chat", addAssistantMessage(successPrediction));
      }
    }
  },
};

export function handleActionMessageWithBridge(message: ActionMessage) {
  const bridge = getQueryReduxBridge();
  
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
    bridge.conditionalDispatch("metrics", setMetrics(metrics));
  }

  if (message.action === ActionType.RUN) {
    bridge.conditionalDispatch("command", appendInput(message.args.command));
  }

  if ("args" in message && "security_risk" in message.args) {
    bridge.conditionalDispatch("securityAnalyzer", appendSecurityAnalyzerInput(message));
  }

  if (message.source === "agent") {
    if (message.args && message.args.thought) {
      bridge.conditionalDispatch("chat", addAssistantMessage(message.args.thought));
    }
    // Need to convert ActionMessage to RejectAction
    // @ts-expect-error TODO: fix
    bridge.conditionalDispatch("chat", addAssistantAction(message));
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleStatusMessageWithBridge(message: StatusMessage) {
  const bridge = getQueryReduxBridge();
  
  if (message.type === "info") {
    bridge.conditionalDispatch(
      "status",
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
    bridge.conditionalDispatch(
      "chat",
      addErrorMessage({
        ...message,
      }),
    );
  }
}

export function handleAssistantMessageWithBridge(message: Record<string, unknown>) {
  if (message.action) {
    handleActionMessageWithBridge(message as unknown as ActionMessage);
  } else if (message.observation) {
    handleObservationMessageWithBridge(message as unknown as ObservationMessage);
  } else if (message.status_update) {
    handleStatusMessageWithBridge(message as unknown as StatusMessage);
  } else {
    const errorMsg = "Unknown message type received";
    trackError({
      message: errorMsg,
      source: "chat",
      metadata: { raw_message: message },
    });
    const bridge = getQueryReduxBridge();
    bridge.conditionalDispatch(
      "chat",
      addErrorMessage({
        message: errorMsg,
      }),
    );
  }
}