import { AppConversationStartTask } from "#/api/open-hands.types";
import DebugStackframeDot from "#/icons/debug-stackframe-dot.svg?react";

interface SetupStatusIndicatorProps {
  task: AppConversationStartTask | null;
  isActive: boolean;
}

export function SetupStatusIndicator({
  task,
  isActive,
}: SetupStatusIndicatorProps) {
  if (!isActive || !task) {
    return null;
  }

  const getStatusMessage = (status: string) => {
    const messages: Record<string, string> = {
      WORKING: "Initializing...",
      WAITING_FOR_SANDBOX: "Setting up environment...",
      PREPARING_REPOSITORY: "Preparing repository...",
      RUNNING_SETUP_SCRIPT: "Running setup...",
      SETTING_UP_GIT_HOOKS: "Configuring git...",
      STARTING_CONVERSATION: "Starting conversation...",
      READY: "Ready",
      ERROR: "Setup failed",
    };
    return messages[status] || status;
  };

  const getStatusColor = (status: string): string => {
    if (status === "ERROR") {
      return "#FF684E"; // Red
    }
    if (status === "READY") {
      return "#BCFF8C"; // Green
    }
    return "#FFD600"; // Yellow for in-progress
  };

  const statusColor = getStatusColor(task.status);
  const statusText = getStatusMessage(task.status);

  return (
    <div className="flex items-center">
      <DebugStackframeDot className="w-6 h-6" color={statusColor} />
      <span className="text-[11px] text-white font-normal leading-5">
        {statusText}
      </span>
    </div>
  );
}
