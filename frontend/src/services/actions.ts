import { trackError } from "#/utils/error-handler";
import useMetricsStore from "#/stores/metrics-store";
import { useStatusStore } from "#/state/status-store";
import ActionType from "#/types/action-type";
import {
  ActionMessage,
  ObservationMessage,
  StatusMessage,
} from "#/types/message";
import { handleObservationMessage } from "./observations";
import { useJupyterStore } from "#/state/jupyter-store";
import { useCommandStore } from "#/state/command-store";
import { queryClient } from "#/query-client-config";
import {
  ActionSecurityRisk,
  useSecurityAnalyzerStore,
} from "#/stores/security-analyzer-store";

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
    useMetricsStore.getState().setMetrics(metrics);
  }

  if (message.action === ActionType.RUN) {
    useCommandStore.getState().appendInput(message.args.command);
  }

  if (message.action === ActionType.RUN_IPYTHON) {
    useJupyterStore.getState().appendJupyterInput(message.args.code);
  }

  if ("args" in message && "security_risk" in message.args) {
    useSecurityAnalyzerStore.getState().appendSecurityAnalyzerInput({
      id: message.id,
      args: {
        command: message.args.command,
        code: message.args.code,
        content: message.args.content,
        security_risk: message.args
          .security_risk as unknown as ActionSecurityRisk,
        confirmation_state: message.args.confirmation_state as
          | "awaiting_confirmation"
          | "confirmed"
          | "rejected"
          | undefined,
      },
      message: message.message,
    });
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
    useStatusStore.getState().setCurStatusMessage({
      ...message,
    });
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
