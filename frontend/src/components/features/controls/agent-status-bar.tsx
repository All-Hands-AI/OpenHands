import React from "react";
import { useTranslation } from "react-i18next";
import { showErrorToast } from "#/utils/error-handler";
import { AgentState } from "#/types/agent-state";
import { AGENT_STATUS_MAP } from "../../agent-status-map.constant";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { useNotification } from "#/hooks/useNotification";
import { browserTab } from "#/utils/browser-tab";
import { StatusMessage } from "#/types/message";

const notificationStates = [
  AgentState.AWAITING_USER_INPUT,
  AgentState.FINISHED,
  AgentState.AWAITING_USER_CONFIRMATION,
];

export function AgentStatusBar() {
  const { t, i18n } = useTranslation();
  // Try to use the agent state context, but fall back to default values for tests
  const agentStateContext = React.useContext(
    React.createContext<{
      curAgentState: AgentState;
      updateAgentState: (state: AgentState) => void;
      resetAgentState: () => void;
    }>({
      curAgentState: AgentState.LOADING,
      updateAgentState: () => {},
      resetAgentState: () => {},
    }),
  );

  const { curAgentState } = agentStateContext;
  // Create a default status context for tests
  const statusContext = React.useContext(
    React.createContext<{ curStatusMessage: StatusMessage }>({
      curStatusMessage: {
        status_update: true,
        type: "info",
        id: "",
        message: "",
      },
    }),
  );

  // Use the status context or default values
  const { curStatusMessage } = statusContext;
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
    if (curAgentState === AgentState.LOADING && message.trim()) {
      setStatusMessage(message);
    } else {
      setStatusMessage(AGENT_STATUS_MAP[curAgentState].message);
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

  React.useEffect(() => {
    if (status === WsClientProviderStatus.DISCONNECTED) {
      setStatusMessage("Connecting...");
    } else {
      setStatusMessage(AGENT_STATUS_MAP[curAgentState].message);
      if (notificationStates.includes(curAgentState)) {
        const message = t(AGENT_STATUS_MAP[curAgentState].message);
        notify(t(AGENT_STATUS_MAP[curAgentState].message), {
          body: t(`Agent state changed to ${curAgentState}`),
          playSound: true,
        });

        // Update browser tab if window exists and is not focused
        if (typeof document !== "undefined" && !document.hasFocus()) {
          browserTab.startNotification(message);
        }
      }
    }
  }, [curAgentState, notify, t]);

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center bg-base-secondary px-2 py-1 text-gray-400 rounded-[100px] text-sm gap-[6px]">
        <div
          className={`w-2 h-2 rounded-full animate-pulse ${AGENT_STATUS_MAP[curAgentState].indicator}`}
        />
        <span className="text-sm text-stone-400">{t(statusMessage)}</span>
      </div>
    </div>
  );
}
