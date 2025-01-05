import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import toast from "react-hot-toast";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { AGENT_STATUS_MAP } from "../../agent-status-map.constant";

export function AgentStatusBar() {
  const { t, i18n } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const { curStatusMessage } = useSelector((state: RootState) => state.status);

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
      toast.error(message);
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

  React.useEffect(() => {
    setStatusMessage(AGENT_STATUS_MAP[curAgentState].message);
  }, [curAgentState]);

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center bg-neutral-800 px-2 py-1 text-gray-400 rounded-[100px] text-sm gap-[6px]">
        <div
          className={`w-2 h-2 rounded-full animate-pulse ${AGENT_STATUS_MAP[curAgentState].indicator}`}
        />
        <span className="text-sm text-stone-400">{t(statusMessage)}</span>
      </div>
    </div>
  );
}
