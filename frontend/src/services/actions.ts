import {
  addAssistantMessage,
  addAssistantAction,
  addUserMessage,
  addErrorMessage,
  appendSecurityAnalyzerInput,
} from "#/types/migrated-types";
import { trackError } from "#/utils/error-handler";
import { OpenHandsAction } from "#/types/core/actions";
// Jupyter slice is now handled by React Query
// Status, metrics, browser, and code slices are now handled by React Query
import store from "#/store";
import { queryClient } from "#/query-redux-bridge-init";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessage } from "./observations";
// Command slice is now handled by React Query

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
    console.log("[Actions Debug] Handling MESSAGE action:", {
      source: message.source,
      content: message.args.content
        ? message.args.content.substring(0, 50) +
          (message.args.content.length > 50 ? "..." : "")
        : "",
      hasImageUrls: !!message.args.image_urls,
    });

    if (message.source === "user") {
      console.log("[Actions Debug] Dispatching addUserMessage");
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
      console.log("[Actions Debug] Dispatching addAssistantMessage");
      store.dispatch(addAssistantMessage(message.args.content));
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
    store.dispatch(addAssistantMessage(message.args.final_thought));
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
        store.dispatch(addAssistantMessage(`\n${successPrediction}`));
      } else {
        store.dispatch(addAssistantMessage(successPrediction));
      }
    }
  },
};

export function handleActionMessage(message: ActionMessage) {
  console.log("[Actions Debug] Handling action message:", {
    action: message.action,
    source: message.source,
    hasThought: !!message.args?.thought,
    message: message.message
      ? message.message.substring(0, 50) +
        (message.message.length > 50 ? "..." : "")
      : "",
  });

  if (message.args?.hidden) {
    console.log("[Actions Debug] Skipping hidden message");
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
    store.dispatch(appendSecurityAnalyzerInput(message));
  }

  if (message.source === "agent") {
    console.log("[Actions Debug] Processing agent message");
    if (message.args && message.args.thought) {
      console.log(
        "[Actions Debug] Dispatching agent thought:",
        message.args.thought.substring(0, 50) +
          (message.args.thought.length > 50 ? "..." : ""),
      );
      store.dispatch(addAssistantMessage(message.args.thought));
    }
    // Need to convert ActionMessage to RejectAction
    console.log("[Actions Debug] Dispatching assistant action");
    store.dispatch(addAssistantAction(message as unknown as OpenHandsAction));
  }

  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleStatusMessage(message: StatusMessage) {
  if (message.type === "info") {
    // Status slice is now handled by React Query
    // The websocket events hook will update the React Query cache
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
  console.log("[Actions Debug] Received assistant message:", {
    hasAction: !!message.action,
    hasObservation: !!message.observation,
    hasStatusUpdate: !!message.status_update,
    messageKeys: Object.keys(message),
  });

  if (message.action) {
    handleActionMessage(message as unknown as ActionMessage);
  } else if (message.observation) {
    console.log("[Actions Debug] Handling observation message");
    handleObservationMessage(message as unknown as ObservationMessage);
  } else if (message.status_update) {
    console.log("[Actions Debug] Handling status message");
    handleStatusMessage(message as unknown as StatusMessage);
  } else {
    console.log("[Actions Debug] Unknown message type received:", message);
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
