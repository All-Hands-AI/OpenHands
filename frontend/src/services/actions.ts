import { trackError } from "#/utils/error-handler";
// Security analyzer, jupyter, status, metrics, browser, code, and chat slices are now handled by React Query
import { queryClient } from "#/query-redux-bridge-init";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessage, getChatFunctions } from "./observations";
// Command slice is now handled by React Query

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      getChatFunctions().addAssistantMessage(message.message);
    }
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    if (!message.args.thought && message.message) {
      getChatFunctions().addAssistantMessage(message.message);
    }
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    // Update code state in React Query
    const currentState = queryClient.getQueryData<{
      code: string;
      path: string;
    }>(["code"]) || { code: "", path: "" };
    queryClient.setQueryData(["code"], {
      ...currentState,
      path,
      code: content,
    });
  },
  [ActionType.MESSAGE]: (message: ActionMessage) => {
    if (message.source === "user") {
      getChatFunctions().addUserMessage({
        content: message.args.content,
        imageUrls:
          typeof message.args.image_urls === "string"
            ? [message.args.image_urls]
            : message.args.image_urls,
        timestamp: message.timestamp,
        pending: false,
      });
    } else {
      getChatFunctions().addAssistantMessage(message.args.content);
    }
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.confirmation_state !== "rejected") {
      // Update jupyter state in React Query
      const currentState = queryClient.getQueryData<{
        cells: Array<{ content: string; type: string }>;
      }>(["jupyter"]) || { cells: [] };

      // eslint-disable-next-line no-console
      console.log("[Jupyter Debug] Handling RUN_IPYTHON action:", {
        code: message.args.code,
        currentCellsLength: currentState.cells.length,
      });

      queryClient.setQueryData(["jupyter"], {
        ...currentState,
        cells: [
          ...currentState.cells,
          { content: message.args.code, type: "input" },
        ],
      });
    }
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    getChatFunctions().addAssistantMessage(message.args.final_thought);
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
        getChatFunctions().addAssistantMessage(`\n${successPrediction}`);
      } else {
        getChatFunctions().addAssistantMessage(successPrediction);
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
    try {
      const bridge = getQueryReduxBridge();
      if (bridge.isSliceMigrated("metrics")) {
        // If metrics slice is migrated, update React Query directly
        bridge.syncReduxToQuery(["metrics"], metrics);
      } else {
        // Otherwise, dispatch to Redux (handled by the bridge)
        bridge.conditionalDispatch("metrics", {
          type: "metrics/setMetrics",
          payload: metrics,
        });
      }
    } catch (error) {
      console.warn("Failed to update metrics:", error);
    }
  }

  if (message.action === ActionType.RUN) {
    // Update command state in React Query
    const currentState = queryClient.getQueryData<{
      commands: Array<{ content: string; type: string }>;
    }>(["command"]) || { commands: [] };

    // eslint-disable-next-line no-console
    console.log("[Command Debug] Handling RUN action:", {
      command: message.args.command,
      currentCommandsLength: currentState.commands.length,
    });

    queryClient.setQueryData(["command"], {
      ...currentState,
      commands: [
        ...currentState.commands,
        { content: message.args.command, type: "input" },
      ],
    });
  }

  if ("args" in message && "security_risk" in message.args) {
    // Security analyzer is now handled by React Query
    // This will be handled by the websocket event handler
  }

  if (message.source === "agent") {
    if (message.args && message.args.thought) {
      getChatFunctions().addAssistantMessage(message.args.thought);
    }
    // Need to convert ActionMessage to RejectAction
    // @ts-expect-error TODO: fix
    getChatFunctions().addAssistantAction(message);
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleStatusMessage(message: StatusMessage) {
  // eslint-disable-next-line no-console
  console.log("[Status Debug] Handling status message:", {
    type: message.type,
    id: message.id,
    message: message.message,
  });

  if (message.type === "info") {
    // Status slice is now handled by React Query
    // The websocket events hook will update the React Query cache
    // Update status message in React Query
    try {
      const queryClient = queryClient;
      // eslint-disable-next-line no-console
      console.log("[Status Debug] Updating status message in React Query");
      queryClient.setQueryData(["status", "currentMessage"], message);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("[Status Debug] Failed to update status message:", error);
    }
  } else if (message.type === "error") {
    trackError({
      message: message.message,
      source: "chat",
      metadata: { msgId: message.id },
    });
    getChatFunctions().addErrorMessage({
      ...message,
    });
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
    getChatFunctions().addErrorMessage({
      message: errorMsg,
    });
  }
}
