import {
  addAssistantMessage,
  addAssistantAction,
  addUserMessage,
  addErrorMessage,
} from "#/services/context-services/chat-service";
import { trackError } from "#/utils/error-handler";
import { appendSecurityAnalyzerInput } from "#/state/security-analyzer-slice";
import { setCode, setActiveFilepath } from "#/state/code-slice";
import { appendJupyterInput } from "#/state/jupyter-slice";
import { handleStatusMessage as handleStatusMessageService } from "#/services/context-services/status-service";
import { updateMetrics as updateMetricsService } from "#/services/context-services/metrics-service";
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
      addAssistantMessage(message.message);
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      addAssistantMessage(message.message);
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
      )
    } else {
      addAssistantMessage(message.args.content))
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      store.dispatch(appendJupyterInput(message.args.code))
    }
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    addAssistantMessage(message.args.final_thought))
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
        addAssistantMessage(`\n${successPrediction}`))
      } else {
        addAssistantMessage(successPrediction))
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
    // Use the metrics service to update metrics
    updateMetricsService(metrics)
  }

  if (message.action === ActionType.RUN) {
    store.dispatch(appendInput(message.args.command))
  }

  if ("args" in message && "security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message))
  }

  if (message.source === "agent") {
    if (message.args && message.args.thought) {
      addAssistantMessage(message.args.thought))
    }
    // Need to convert ActionMessage to RejectAction
    // @ts-expect-error TODO: fix
    addAssistantAction(message))
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message)
  }
}

export function handleStatusMessage(message: StatusMessage) {
  // Use the status service to handle the message
  handleStatusMessageService(message)
}

export function handleAssistantMessage(message: Record<string, unknown>) {
  if (message.action) {
    handleActionMessage(message as unknown as ActionMessage)
  } else if (message.observation) {
    handleObservationMessage(message as unknown as ObservationMessage)
  } else if (message.status_update) {
    handleStatusMessage(message as unknown as StatusMessage)
  } else {
    const errorMsg = "Unknown message type received";
    trackError({
      message: errorMsg,
      source: "chat",
      metadata: { raw_message: message },
    })
    store.dispatch(
      addErrorMessage({
        message: errorMsg,
      }),
    )
  }
}
