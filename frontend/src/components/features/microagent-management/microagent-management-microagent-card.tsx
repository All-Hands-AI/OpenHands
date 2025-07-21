import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { formatDateMMDDYYYY } from "#/utils/format-time-delta";
import {
  EventMicroagentStatus,
  MicroagentStatus,
} from "#/types/microagent-status";
import { ConversationStatus } from "#/types/conversation-status";
import { RuntimeStatus } from "#/types/runtime-status";

interface MicroagentManagementMicroagentCardProps {
  microagent: {
    id: string;
    name: string;
    createdAt: string;
    conversationStatus?: ConversationStatus;
    runtimeStatus?: RuntimeStatus;
    prNumber?: number[] | null;
  };
  showMicroagentFilePath?: boolean;
  microagentStatus?: EventMicroagentStatus;
}

export function MicroagentManagementMicroagentCard({
  microagent,
  showMicroagentFilePath = true,
  microagentStatus,
}: MicroagentManagementMicroagentCardProps) {
  const { t } = useTranslation();

  const { conversationStatus, runtimeStatus, prNumber } = microagent;

  // Format the repository URL to point to the microagent file
  const microagentFilePath = `.openhands/microagents/${microagent.name}`;

  // Format the createdAt date using MM/DD/YYYY format
  const formattedCreatedAt = formatDateMMDDYYYY(new Date(microagent.createdAt));

  const hasPr = prNumber && prNumber.length > 0;

  const isOpeningPRStatus = () =>
    ((conversationStatus === "STARTING" || conversationStatus === "RUNNING") &&
      runtimeStatus === "STATUS$READY") ||
    microagentStatus?.status === MicroagentStatus.CREATING;

  const isCompletedStatus = () =>
    hasPr || microagentStatus?.status === MicroagentStatus.COMPLETED;

  const isStoppedStatus = () =>
    conversationStatus === "STOPPED" || runtimeStatus === "STATUS$STOPPED";

  const isErrorStatus = () =>
    runtimeStatus === "STATUS$ERROR" ||
    microagentStatus?.status === MicroagentStatus.ERROR;

  // Helper function to get status text
  const statusText = useMemo(() => {
    if (isStoppedStatus()) {
      return t(I18nKey.COMMON$STOPPED);
    }
    if (isErrorStatus()) {
      return t(I18nKey.MICROAGENT$STATUS_ERROR);
    }
    if (isCompletedStatus()) {
      return hasPr || microagentStatus?.prUrl
        ? t(I18nKey.COMMON$READY_FOR_REVIEW)
        : t(I18nKey.COMMON$COMPLETED_PARTIALLY);
    }
    if (isOpeningPRStatus()) {
      return t(I18nKey.MICROAGENT$STATUS_OPENING_PR);
    }
    return "";
  }, [microagentStatus, conversationStatus, runtimeStatus, t]);

  return (
    <div className="rounded-lg bg-[#ffffff0d] border border-[#ffffff33] p-4 cursor-pointer hover:bg-[#ffffff33] hover:border-[#C9B974] transition-all duration-300">
      <div className="flex flex-col items-start gap-2">
        {statusText && (
          <div className="px-[6px] py-[2px] text-[11px] font-medium bg-[#C9B97433] text-white rounded-2xl">
            {statusText}
          </div>
        )}
        <div className="text-white text-[16px] font-semibold">
          {microagent.name}
        </div>
        {showMicroagentFilePath && (
          <div className="text-white text-sm font-normal">
            {microagentFilePath}
          </div>
        )}
        <div className="text-white text-sm font-normal">
          {t(I18nKey.COMMON$CREATED_ON)} {formattedCreatedAt}
        </div>
      </div>
    </div>
  );
}
