import { AppConversationStartTask } from "#/api/open-hands.types";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

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
      READY: "Ready!",
      ERROR: "Setup failed",
    };
    return messages[status] || status;
  };

  const getProgressPercentage = (status: string) => {
    const progress: Record<string, number> = {
      WORKING: 10,
      WAITING_FOR_SANDBOX: 25,
      PREPARING_REPOSITORY: 50,
      RUNNING_SETUP_SCRIPT: 70,
      SETTING_UP_GIT_HOOKS: 85,
      STARTING_CONVERSATION: 95,
      READY: 100,
      ERROR: 0,
    };
    return progress[status] || 0;
  };

  const isError = task.status === "ERROR";
  const isReady = task.status === "READY";
  const isInProgress = !isError && !isReady;

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
      {/* Progress indicator */}
      {isInProgress && <LoadingSpinner size="small" />}

      {/* Status icon for completed/error states */}
      {isReady && (
        <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">
          ✓
        </div>
      )}
      {isError && (
        <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center text-white text-xs">
          ✕
        </div>
      )}

      {/* Status message and progress bar */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span
            className={`text-sm font-medium ${
              isError
                ? "text-red-700"
                : isReady
                  ? "text-green-700"
                  : "text-blue-700"
            }`}
          >
            {getStatusMessage(task.status)}
          </span>
          <span className="text-xs text-gray-500 whitespace-nowrap">
            {getProgressPercentage(task.status)}%
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all duration-500 ${
              isError
                ? "bg-red-500"
                : isReady
                  ? "bg-green-500"
                  : "bg-blue-500"
            }`}
            style={{ width: `${getProgressPercentage(task.status)}%` }}
          />
        </div>

        {/* Detail message if available */}
        {task.detail && (
          <p className="text-xs text-gray-600 mt-1 truncate">{task.detail}</p>
        )}
      </div>
    </div>
  );
}
