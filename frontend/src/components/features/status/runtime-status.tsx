import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import ServerProcessIcon from "#/icons/server-process.svg?react";

export interface RuntimeStatusProps {
  className?: string;
}

export function RuntimeStatus({ className = "" }: RuntimeStatusProps) {
  const { t } = useTranslation();
  const { data: conversation } = useActiveConversation();
  const runtimeStatus = conversation?.runtime_status;

  // Get status color based on runtime status
  const getStatusColor = (): string => {
    if (!runtimeStatus) return "#9CA3AF"; // Gray for unknown

    switch (runtimeStatus) {
      case "STATUS$READY":
      case "STATUS$RUNTIME_STARTED":
        return "#BCFF8C"; // Green
      case "STATUS$BUILDING_RUNTIME":
      case "STATUS$STARTING_RUNTIME":
      case "STATUS$SETTING_UP_WORKSPACE":
      case "STATUS$SETTING_UP_GIT_HOOKS":
      case "STATUS$LLM_RETRY":
        return "#FFD600"; // Yellow
      case "STATUS$STOPPED":
        return "#9CA3AF"; // Gray
      case "STATUS$ERROR":
      case "STATUS$ERROR_RUNTIME_DISCONNECTED":
      case "STATUS$ERROR_LLM_AUTHENTICATION":
      case "STATUS$ERROR_LLM_SERVICE_UNAVAILABLE":
      case "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR":
      case "STATUS$ERROR_LLM_OUT_OF_CREDITS":
      case "STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION":
      case "STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR":
      case "STATUS$ERROR_MEMORY":
        return "#FF684E"; // Red
      case "CHAT_INTERFACE$AGENT_RATE_LIMITED_STOPPED_MESSAGE":
        return "#FFA500"; // Orange
      default:
        return "#9CA3AF"; // Gray
    }
  };

  // Get status text based on runtime status
  const getStatusText = (): string => {
    if (!runtimeStatus) return "Runtime Unknown";

    // Try to get translated text from I18nKey
    const translationKey = (I18nKey as { [key: string]: string })[
      runtimeStatus
    ];
    if (translationKey) {
      return t(translationKey);
    }

    // Fallback to human-readable format
    switch (runtimeStatus) {
      case "STATUS$READY":
        return "Runtime Ready";
      case "STATUS$RUNTIME_STARTED":
        return "Runtime Started";
      case "STATUS$BUILDING_RUNTIME":
        return "Building Runtime";
      case "STATUS$STARTING_RUNTIME":
        return "Starting Runtime";
      case "STATUS$SETTING_UP_WORKSPACE":
        return "Setting up Workspace";
      case "STATUS$SETTING_UP_GIT_HOOKS":
        return "Setting up Git Hooks";
      case "STATUS$STOPPED":
        return "Runtime Stopped";
      case "STATUS$ERROR":
        return "Runtime Error";
      case "STATUS$ERROR_RUNTIME_DISCONNECTED":
        return "Runtime Disconnected";
      case "STATUS$ERROR_LLM_AUTHENTICATION":
        return "LLM Authentication Error";
      case "STATUS$ERROR_LLM_SERVICE_UNAVAILABLE":
        return "LLM Service Unavailable";
      case "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR":
        return "LLM Internal Error";
      case "STATUS$ERROR_LLM_OUT_OF_CREDITS":
        return "LLM Out of Credits";
      case "STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION":
        return "LLM Content Policy Violation";
      case "STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR":
        return "Git Authentication Error";
      case "STATUS$LLM_RETRY":
        return "LLM Retrying";
      case "STATUS$ERROR_MEMORY":
        return "Memory Error";
      case "CHAT_INTERFACE$AGENT_RATE_LIMITED_STOPPED_MESSAGE":
        return "Agent Rate Limited";
      default:
        // Handle unexpected runtime status values by formatting them
        return (runtimeStatus as string)
          .replace("STATUS$", "")
          .replace(/_/g, " ");
    }
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();

  return (
    <div className={className}>
      <Tooltip content={statusText} closeDelay={100}>
        <div className="flex items-center">
          <ServerProcessIcon
            className="w-4 h-4"
            style={{ color: statusColor }}
          />
        </div>
      </Tooltip>
    </div>
  );
}

export default RuntimeStatus;
