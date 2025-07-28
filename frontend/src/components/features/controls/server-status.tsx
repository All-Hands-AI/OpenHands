import { Typography } from "@openhands/ui";
import { useTranslation } from "react-i18next";
import DebugStackframeDot from "#/icons/debug-stackframe-dot.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatus } from "#/types/conversation-status";

export interface ServerStatusProps {
  conversationStatus: ConversationStatus | null;
  className?: string;
}

export function ServerStatus({
  conversationStatus,
  className = "",
}: ServerStatusProps) {
  const { t } = useTranslation();

  // Get the appropriate color based on conversation status
  const getStatusColor = (status: ConversationStatus | null): string => {
    if (!status) return "#959CB2"; // Default gray color

    switch (status) {
      case "STARTING":
        return "#F59E0B"; // Yellow for starting
      case "RUNNING":
        return "#10B981"; // Green for running
      case "STOPPED":
        return "#EF4444"; // Red for stopped
      default:
        return "#959CB2"; // Default gray
    }
  };

  // Get the appropriate status text based on conversation status
  const getStatusText = (status: ConversationStatus | null): string => {
    if (!status) return "Unknown";

    switch (status) {
      case "STARTING":
        return t(I18nKey.COMMON$STARTING);
      case "RUNNING":
        return t(I18nKey.COMMON$RUNNING);
      case "STOPPED":
        return t(I18nKey.CHAT_INTERFACE$STOPPED);
      default:
        return t(I18nKey.COMMON$UNKNOWN);
    }
  };

  const statusColor = getStatusColor(conversationStatus);
  const statusText = getStatusText(conversationStatus);

  return (
    <div className={`flex items-center ${className}`}>
      <DebugStackframeDot className="w-6 h-6" color={statusColor} />
      <Typography.Text className="text-[11px] text-[#D0D9FA] font-normal leading-5">
        {statusText}
      </Typography.Text>
    </div>
  );
}

export default ServerStatus;
