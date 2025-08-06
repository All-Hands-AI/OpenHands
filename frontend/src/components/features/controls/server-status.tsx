import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import DebugStackframeDot from "#/icons/debug-stackframe-dot.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatus } from "#/types/conversation-status";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";

export interface ServerStatusProps {
  className?: string;
  conversationStatus: ConversationStatus | null;
}

export function ServerStatus({
  className = "",
  conversationStatus,
}: ServerStatusProps) {
  const { t } = useTranslation();

  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const isStopStatus =
    curAgentState === AgentState.STOPPED || conversationStatus === "STOPPED";

  // Get the appropriate color based on agent status
  const getStatusColor = (): string => {
    if (isStopStatus) {
      return "#ffffff";
    }
    if (curAgentState === AgentState.ERROR) {
      return "#FF684E";
    }
    return "#BCFF8C";
  };

  // Get the appropriate status text based on agent status
  const getStatusText = (): string => {
    if (isStopStatus) {
      return t(I18nKey.COMMON$SERVER_STOPPED);
    }
    if (curAgentState === AgentState.ERROR) {
      return t(I18nKey.COMMON$ERROR);
    }
    return t(I18nKey.COMMON$RUNNING);
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();

  return (
    <div className={`flex items-center ${className}`}>
      <DebugStackframeDot className="w-6 h-6" color={statusColor} />
      <span className="text-[11px] text-white font-normal leading-5">
        {statusText}
      </span>
    </div>
  );
}

export default ServerStatus;
