import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import RobotIcon from "#/icons/robot.svg?react";

export interface AgentStatusProps {
  className?: string;
}

export function AgentStatus({ className = "" }: AgentStatusProps) {
  const { t } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  // Get status color based on agent state
  const getStatusColor = (): string => {
    switch (curAgentState) {
      case AgentState.LOADING:
      case AgentState.INIT:
        return "#FFD600"; // Yellow
      case AgentState.RUNNING:
        return "#60A5FA"; // Blue
      case AgentState.AWAITING_USER_INPUT:
      case AgentState.AWAITING_USER_CONFIRMATION:
      case AgentState.USER_CONFIRMED:
      case AgentState.USER_REJECTED:
      case AgentState.FINISHED:
        return "#BCFF8C"; // Green
      case AgentState.STOPPED:
      case AgentState.PAUSED:
      case AgentState.REJECTED:
        return "#9CA3AF"; // Gray
      case AgentState.ERROR:
      case AgentState.RATE_LIMITED:
        return "#FF684E"; // Red
      default:
        return "#9CA3AF"; // Default gray
    }
  };

  // Get status text based on agent state
  const getStatusText = (): string => {
    switch (curAgentState) {
      case AgentState.LOADING:
      case AgentState.INIT:
        return t(I18nKey.AGENT_STATUS$INITIALIZING);
      case AgentState.RUNNING:
        return t(I18nKey.AGENT_STATUS$RUNNING_TASK);
      case AgentState.AWAITING_USER_INPUT:
      case AgentState.AWAITING_USER_CONFIRMATION:
      case AgentState.USER_CONFIRMED:
      case AgentState.USER_REJECTED:
      case AgentState.FINISHED:
        return t(I18nKey.AGENT_STATUS$WAITING_FOR_TASK);
      case AgentState.STOPPED:
      case AgentState.PAUSED:
      case AgentState.REJECTED:
        return t(I18nKey.AGENT_STATUS$AGENT_STOPPED);
      case AgentState.ERROR:
      case AgentState.RATE_LIMITED:
        return t(I18nKey.AGENT_STATUS$ERROR_OCCURRED);
      default:
        return "Unknown Agent State";
    }
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();

  return (
    <div className={className}>
      <Tooltip className="capitalize" content={statusText} closeDelay={100}>
        <div className="flex items-center">
          <RobotIcon className="w-4 h-4" style={{ color: statusColor }} />
        </div>
      </Tooltip>
    </div>
  );
}

export default AgentStatus;
