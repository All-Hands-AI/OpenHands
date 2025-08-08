import { useSelector, useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import DebugStackframeDot from "#/icons/debug-stackframe-dot.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatus } from "#/types/conversation-status";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { ServerStatusContextMenu } from "./server-status-context-menu";
import {
  setShouldStopConversation,
  setShouldStartConversation,
} from "#/state/conversation-slice";

export interface ServerStatusProps {
  className?: string;
  conversationStatus: ConversationStatus | null;
}

export function ServerStatus({
  className = "",
  conversationStatus,
}: ServerStatusProps) {
  const { t } = useTranslation();
  const [showContextMenu, setShowContextMenu] = useState(false);
  const dispatch = useDispatch();

  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const isStartingStatus =
    curAgentState === AgentState.LOADING || curAgentState === AgentState.INIT;

  const isStopStatus =
    curAgentState === AgentState.STOPPED || conversationStatus === "STOPPED";

  // Get the appropriate color based on agent status
  const getStatusColor = (): string => {
    if (isStartingStatus) {
      return "#FFD600";
    }
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
    if (isStartingStatus) {
      return t(I18nKey.COMMON$STARTING);
    }
    if (isStopStatus) {
      return t(I18nKey.COMMON$SERVER_STOPPED);
    }
    if (curAgentState === AgentState.ERROR) {
      return t(I18nKey.COMMON$ERROR);
    }
    return t(I18nKey.COMMON$RUNNING);
  };

  const handleClick = () => {
    if (conversationStatus === "RUNNING" || conversationStatus === "STOPPED") {
      setShowContextMenu(true);
    }
  };

  const handleCloseContextMenu = () => {
    setShowContextMenu(false);
  };

  const handleStopServer = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    dispatch(setShouldStopConversation(true));
    setShowContextMenu(false);
  };

  const handleStartServer = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    dispatch(setShouldStartConversation(true));
    setShowContextMenu(false);
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center cursor-pointer" onClick={handleClick}>
        <DebugStackframeDot className="w-6 h-6" color={statusColor} />
        <span className="text-[11px] text-white font-normal leading-5">
          {statusText}
        </span>
      </div>

      {showContextMenu && (
        <ServerStatusContextMenu
          onClose={handleCloseContextMenu}
          onStopServer={handleStopServer}
          onStartServer={handleStartServer}
          conversationStatus={conversationStatus}
          position="top"
        />
      )}
    </div>
  );
}

export default ServerStatus;
