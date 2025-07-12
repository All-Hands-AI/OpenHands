import { trackError } from "#/utils/error-handler";
import { appendSecurityAnalyzerInput } from "#/state/security-analyzer-slice";
import { setCurStatusMessage } from "#/state/status-slice";
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
import { appendJupyterInput } from "#/state/jupyter-slice";
import { queryClient } from "#/query-client-config";

export function handleActionMessage(message: ActionMessage) {
  if (message.args?.hidden) {
    return;
  }

  // Update metrics if available
  if (message.llm_metrics) {
    const metrics = {
      cost: message.llm_metrics?.accumulated_cost ?? null,
      max_budget_per_task: message.llm_metrics?.max_budget_per_task ?? null,
      usage: message.llm_metrics?.accumulated_token_usage ?? null,
    };
    store.dispatch(setMetrics(metrics));
  }

  if (message.action === ActionType.RUN) {
    store.dispatch(appendInput(message.args.command));
  }

  if (message.action === ActionType.RUN_IPYTHON) {
    store.dispatch(appendJupyterInput(message.args.code));
  }

  if ("args" in message && "security_risk" in message.args) {
    store.dispatch(appendSecurityAnalyzerInput(message));
  }
}

export function handleStatusMessage(message: StatusMessage) {
  // Info message with conversation_title indicates new title for conversation
  if (message.type === "info" && message.conversation_title) {
    const conversationId = message.message;

    // Invalidate the conversation query to trigger a refetch with the new title
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
  } else if (message.type === "info") {
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
  }
}

export function handleAssistantMessage(message: Record<string, unknown>) {
  if (message.action) {
    handleActionMessage(message as unknown as ActionMessage);
  } else if (message.observation) {
    handleObservationMessage(message as unknown as ObservationMessage);
  } else if (message.status_update) {
    handleStatusMessage(message as unknown as StatusMessage);
  }
}
