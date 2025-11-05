import { useTranslation } from "react-i18next";
import { useState } from "react";
import DebugStackframeDot from "#/icons/debug-stackframe-dot.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatus } from "#/types/conversation-status";
import { AgentState } from "#/types/agent-state";
import { ServerStatusContextMenu } from "./server-status-context-menu";
import { useAgentState } from "#/hooks/use-agent-state";
import { useTaskPolling } from "#/hooks/query/use-task-polling";

export interface ServerStatusProps {
  className?: string;
  conversationStatus: ConversationStatus | null;
  isPausing?: boolean;
  handleStop: () => void;
  handleResumeAgent: () => void;
}

export function ServerStatus({
  className = "",
  conversationStatus,
  isPausing = false,
  handleStop,
  handleResumeAgent,
}: ServerStatusProps) {
  const [showContextMenu, setShowContextMenu] = useState(false);

  const { curAgentState } = useAgentState();
  const { t } = useTranslation();
  const { isTask, taskStatus, taskDetail } = useTaskPolling();

  const isStartingStatus =
    curAgentState === AgentState.LOADING || curAgentState === AgentState.INIT;

  const isStopStatus = conversationStatus === "STOPPED";

  // Get the appropriate color based on agent status
  const getStatusColor = (): string => {
    // Show pausing status
    if (isPausing) {
      return "#FFD600";
    }

    // Show task status if we're polling a task
    if (isTask && taskStatus) {
      if (taskStatus === "ERROR") {
        return "#FF684E";
      }
      return "#FFD600";
    }

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
    // Show pausing status
    if (isPausing) {
      return t(I18nKey.COMMON$STOPPING);
    }

    // Show task status if we're polling a task
    if (isTask && taskStatus) {
      if (taskStatus === "ERROR") {
        return (
          taskDetail || t(I18nKey.CONVERSATION$ERROR_STARTING_CONVERSATION)
        );
      }
      if (taskStatus === "READY") {
        return t(I18nKey.CONVERSATION$READY);
      }
      // Format status text: "WAITING_FOR_SANDBOX" -> "Waiting for sandbox"
      return (
        taskDetail ||
        taskStatus
          .toLowerCase()
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase())
      );
    }

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
    handleStop();
    setShowContextMenu(false);
  };

  const handleStartServer = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    handleResumeAgent();
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
