import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { showErrorToast } from "#/utils/error-handler";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import {
  AGENT_STATUS_MAP,
  IndicatorColor,
} from "../../agent-status-map.constant";
import { useWsClient, WebSocketStatus } from "#/context/ws-client-provider";
import { useNotification } from "#/hooks/useNotification";
import { browserTab } from "#/utils/browser-tab";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { ConversationStatus } from "#/types/conversation-status";
import { RuntimeStatus } from "#/types/runtime-status";
import { StatusMessage } from "#/types/message";

const notificationStates = [
  AgentState.AWAITING_USER_INPUT,
  AgentState.FINISHED,
  AgentState.AWAITING_USER_CONFIRMATION,
];

function getIndicatorColor(
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
    [AgentState.PAUSED, AgentState.REJECTED, AgentState.RATE_LIMITED].includes(
      agentState as AgentState,
    )
  ) {
    return IndicatorColor.YELLOW;
  }

  if ([AgentState.LOADING].includes(agentState as AgentState)) {
    return IndicatorColor.DARK_ORANGE;
  }

  if (
    [AgentState.AWAITING_USER_CONFIRMATION].includes(agentState as AgentState)
  ) {
    return IndicatorColor.ORANGE;
  }

  if (agentState === AgentState.AWAITING_USER_INPUT) {
    return IndicatorColor.BLUE;
  }

  // All other agent states are green
  return IndicatorColor.GREEN;
}

function getStatusCode(
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

  if (statusMessage?.id && statusMessage.id !== "STATUS$READY") {
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

export function AgentStatusBar() {
  const { t, i18n } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const { curStatusMessage } = useSelector((state: RootState) => state.status);
  const { webSocketStatus } = useWsClient();
  const { data: conversation } = useActiveConversation();
  const indicatorColor = getIndicatorColor(
    webSocketStatus,
    conversation?.status || null,
    conversation?.runtime_status || null,
    curAgentState,
  );
  const statusCode = getStatusCode(
    curStatusMessage,
    webSocketStatus,
    conversation?.status || null,
    conversation?.runtime_status || null,
    curAgentState,
  );
  const { notify } = useNotification();

  // Show error toast if required
  React.useEffect(() => {
    if (curStatusMessage?.type !== "error") {
      return;
    }
    let message = curStatusMessage.message || "";
    if (curStatusMessage?.id) {
      const id = curStatusMessage.id.trim();
      if (id === "STATUS$READY") {
        message = "awaiting_user_input";
      }
      if (i18n.exists(id)) {
        message = t(curStatusMessage.id.trim()) || message;
      }
    }
    showErrorToast({
      message,
      source: "agent-status",
      metadata: { ...curStatusMessage },
    });
  }, [curStatusMessage.id]);

  // Handle notify
  React.useEffect(() => {
    if (notificationStates.includes(curAgentState)) {
      const message = t(statusCode);
      notify(message, {
        body: t(`Agent state changed to ${curAgentState}`),
        playSound: true,
      });

      // Update browser tab if window exists and is not focused
      if (typeof document !== "undefined" && !document.hasFocus()) {
        browserTab.startNotification(message);
      }
    }
  }, [curAgentState, statusCode]);

  // Handle window focus/blur
  React.useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const handleFocus = () => {
      browserTab.stopNotification();
    };

    window.addEventListener("focus", handleFocus);
    return () => {
      window.removeEventListener("focus", handleFocus);
      browserTab.stopNotification();
    };
  }, []);

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center bg-base-secondary px-2 py-1 text-gray-400 rounded-[100px] text-sm gap-[6px]">
        <div
          className={`w-2 h-2 rounded-full animate-pulse ${indicatorColor}`}
        />
        <span className="text-sm text-stone-400">{t(statusCode)}</span>
      </div>
    </div>
  );
}
