import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { showErrorToast } from "#/utils/error-handler";
import { AgentState } from "#/types/agent-state";
import {
  AGENT_STATUS_MAP,
  IndicatorColor,
} from "../../agent-status-map.constant";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { useNotification } from "#/hooks/useNotification";
import { browserTab } from "#/utils/browser-tab";
import { useAgentState } from "#/hooks/state/use-agent-state";
import { RootState } from "#/store";

const notificationStates = [
  AgentState.AWAITING_USER_INPUT,
  AgentState.FINISHED,
  AgentState.AWAITING_USER_CONFIRMATION,
];

export function AgentStatusBar() {
  const { t, i18n } = useTranslation();
  const { curStatusMessage } = useSelector((state: RootState) => state.status);
  const { agentState } = useAgentState();
  const { status } = useWsClient();
  const { notify } = useNotification();

  const [statusMessage, setStatusMessage] = React.useState<string>("");

  const updateStatusMessage = () => {
    let message = curStatusMessage.message || "";
    if (curStatusMessage?.id) {
      const id = curStatusMessage.id.trim();
      if (i18n.exists(id)) {
        message = t(curStatusMessage.id.trim()) || message;
      }
    }
    if (curStatusMessage?.type === "error") {
      showErrorToast({
        message,
        source: "agent-status",
        metadata: { ...curStatusMessage },
      });
      return;
    }
    if (agentState === AgentState.LOADING && message.trim()) {
      setStatusMessage(message);
    } else {
      setStatusMessage(AGENT_STATUS_MAP[agentState].message);
    }
  };

  React.useEffect(() => {
    updateStatusMessage();
  }, [curStatusMessage.id]);

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

  const [indicatorColor, setIndicatorColor] = React.useState<string>(
    AGENT_STATUS_MAP[agentState].indicator,
  );

  React.useEffect(() => {
    if (status === WsClientProviderStatus.DISCONNECTED) {
      setStatusMessage("Connecting...");
      setIndicatorColor(IndicatorColor.RED);
    } else {
      setStatusMessage(AGENT_STATUS_MAP[agentState].message);
      setIndicatorColor(AGENT_STATUS_MAP[agentState].indicator);
      if (notificationStates.includes(agentState)) {
        const message = t(AGENT_STATUS_MAP[agentState].message);
        notify(t(AGENT_STATUS_MAP[agentState].message), {
          body: t(`Agent state changed to ${agentState}`),
          playSound: true,
        });

        // Update browser tab if window exists and is not focused
        if (typeof document !== "undefined" && !document.hasFocus()) {
          browserTab.startNotification(message);
        }
      }
    }
  }, [agentState, status, notify, t]);

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center bg-base-secondary px-2 py-1 text-gray-400 rounded-[100px] text-sm gap-[6px]">
        <div
          className={`w-2 h-2 rounded-full animate-pulse ${indicatorColor}`}
        />
        <span className="text-sm text-stone-400">{t(statusMessage)}</span>
      </div>
    </div>
  );
}
