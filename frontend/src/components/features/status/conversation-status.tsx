import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatus as ConversationStatusType } from "#/types/conversation-status";
import ServerIcon from "#/icons/server.svg?react";

export interface ConversationStatusProps {
  className?: string;
  conversationStatus: ConversationStatusType | null;
}

export function ConversationStatus({
  className = "",
  conversationStatus,
}: ConversationStatusProps) {
  const { t } = useTranslation();

  // Get status color based on conversation status
  const getStatusColor = (): string => {
    switch (conversationStatus) {
      case "STARTING":
        return "#FFD600"; // Yellow
      case "RUNNING":
        return "#BCFF8C"; // Green
      case "STOPPED":
        return "#9CA3AF"; // Gray
      case "ERROR":
        return "#FF684E"; // Red
      case "ARCHIVED":
        return "#6B7280"; // Dark gray
      default:
        return "#9CA3AF"; // Default gray
    }
  };

  // Get status text based on conversation status
  const getStatusText = (): string => {
    switch (conversationStatus) {
      case "STARTING":
        return t(I18nKey.COMMON$STARTING);
      case "RUNNING":
        return t(I18nKey.COMMON$RUNNING);
      case "STOPPED":
        return t(I18nKey.COMMON$SERVER_STOPPED);
      case "ERROR":
        return t(I18nKey.COMMON$ERROR);
      case "ARCHIVED":
        return "Archived";
      default:
        return "Unknown";
    }
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();

  return (
    <div className={className}>
      <Tooltip content={`Conversation ${statusText}`} closeDelay={100}>
        <div className="flex items-center">
          <ServerIcon className="w-4 h-4" style={{ color: statusColor }} />
        </div>
      </Tooltip>
    </div>
  );
}

export default ConversationStatus;
