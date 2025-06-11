import { WebSocketStatus } from "#/context/ws-client-provider";
import { I18nKey } from "#/i18n/declaration";
import { AgentState } from "#/types/agent-state";
import { ConversationStatus } from "#/types/conversation-status";
import { StatusMessage } from "#/types/message";
import { RuntimeStatus } from "#/types/runtime-status";

export enum IndicatorColor {
  BLUE = "bg-blue-500",
  GREEN = "bg-green-500",
  ORANGE = "bg-orange-500",
  YELLOW = "bg-yellow-500",
  RED = "bg-red-500",
  DARK_ORANGE = "bg-orange-800",
}

export const AGENT_STATUS_MAP: {
  [k: string]: string;
} = {
  [AgentState.INIT]: I18nKey.CHAT_INTERFACE$AGENT_INIT_MESSAGE,
  [AgentState.RUNNING]: I18nKey.CHAT_INTERFACE$AGENT_RUNNING_MESSAGE,
  [AgentState.AWAITING_USER_INPUT]:
    I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_INPUT_MESSAGE,
  [AgentState.PAUSED]: I18nKey.CHAT_INTERFACE$AGENT_PAUSED_MESSAGE,
  [AgentState.LOADING]:
    I18nKey.CHAT_INTERFACE$INITIALIZING_AGENT_LOADING_MESSAGE,
  [AgentState.STOPPED]: I18nKey.CHAT_INTERFACE$AGENT_STOPPED_MESSAGE,
  [AgentState.FINISHED]: I18nKey.CHAT_INTERFACE$AGENT_FINISHED_MESSAGE,
  [AgentState.REJECTED]: I18nKey.CHAT_INTERFACE$AGENT_REJECTED_MESSAGE,
  [AgentState.ERROR]: I18nKey.CHAT_INTERFACE$AGENT_ERROR_MESSAGE,
  [AgentState.AWAITING_USER_CONFIRMATION]:
    I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_CONFIRMATION_MESSAGE,
  [AgentState.USER_CONFIRMED]:
    I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_CONFIRMED_MESSAGE,
  [AgentState.USER_REJECTED]:
    I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_REJECTED_MESSAGE,
  [AgentState.RATE_LIMITED]: I18nKey.CHAT_INTERFACE$AGENT_RATE_LIMITED_MESSAGE,
};

export function getIndicatorColor(
  webSocketStatus: WebSocketStatus,
  conversationStatus: ConversationStatus | null,
  runtimeStatus: RuntimeStatus | null,
  agentState: AgentState | null,
) {
  if (
    webSocketStatus === "DISCONNECTED" ||
    conversationStatus === "STOPPED" ||
    runtimeStatus === "STATUS$STOPPED" ||
    agentState === AgentState.STOPPED
  ) {
    return IndicatorColor.RED;
  }
  // Display a yellow working icon while the runtime is starting
  if (
    conversationStatus === "STARTING" ||
    !["STATUS$READY", null].includes(runtimeStatus) ||
    (agentState != null &&
      [
        AgentState.LOADING,
        AgentState.PAUSED,
        AgentState.REJECTED,
        AgentState.RATE_LIMITED,
      ].includes(agentState))
  ) {
    return IndicatorColor.YELLOW;
  }

  if (agentState === AgentState.AWAITING_USER_CONFIRMATION) {
    return IndicatorColor.ORANGE;
  }

  if (agentState === AgentState.AWAITING_USER_INPUT) {
    return IndicatorColor.BLUE;
  }

  // All other agent states are green
  return IndicatorColor.GREEN;
}

export function getStatusCode(
  statusMessage: StatusMessage,
  webSocketStatus: WebSocketStatus,
  conversationStatus: ConversationStatus | null,
  runtimeStatus: RuntimeStatus | null,
  agentState: AgentState | null,
) {
  if (conversationStatus === "STOPPED" || runtimeStatus === "STATUS$STOPPED") {
    return I18nKey.CHAT_INTERFACE$STOPPED;
  }
  if (runtimeStatus === "STATUS$BUILDING_RUNTIME") {
    return I18nKey.STATUS$BUILDING_RUNTIME;
  }
  if (runtimeStatus === "STATUS$STARTING_RUNTIME") {
    return I18nKey.STATUS$STARTING_RUNTIME;
  }
  if (webSocketStatus === "DISCONNECTED") {
    return I18nKey.CHAT_INTERFACE$DISCONNECTED;
  }
  if (webSocketStatus === "CONNECTING") {
    return I18nKey.CHAT_INTERFACE$CONNECTING;
  }

  if (
    agentState === AgentState.LOADING &&
    statusMessage?.id &&
    statusMessage.id !== "STATUS$READY"
  ) {
    return statusMessage.id;
  }

  if (agentState) {
    return AGENT_STATUS_MAP[agentState];
  }

  if (runtimeStatus && runtimeStatus !== "STATUS$READY" && !agentState) {
    return runtimeStatus;
  }

  return "STATUS$ERROR"; // illegal state
}
