import { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { formatDateMMDDYYYY } from "#/utils/format-time-delta";
import {
  EventMicroagentStatus,
  MicroagentStatus,
} from "#/types/microagent-status";
import { RepositoryMicroagent } from "#/types/microagent-management";
import { Conversation } from "#/api/open-hands.types";
import {
  setSelectedMicroagentItem,
  setSelectedRepository,
} from "#/state/microagent-management-slice";
import { RootState } from "#/store";
import { cn } from "#/utils/utils";
import { GitRepository } from "#/types/git";

interface MicroagentManagementMicroagentCardProps {
  microagent?: RepositoryMicroagent;
  conversation?: Conversation;
  microagentStatus?: EventMicroagentStatus;
  repository: GitRepository;
}

export function MicroagentManagementMicroagentCard({
  microagent,
  conversation,
  microagentStatus,
  repository,
}: MicroagentManagementMicroagentCardProps) {
  const { t } = useTranslation();

  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const dispatch = useDispatch();

  const {
    status: conversationStatus,
    runtime_status: runtimeStatus,
    pr_number: prNumber,
  } = conversation ?? {};

  // Format the repository URL to point to the microagent file
  const microagentFilePath = microagent
    ? `.openhands/microagents/${microagent.name}`
    : "";

  // Format the createdAt date using MM/DD/YYYY format
  const formattedCreatedAt = microagent
    ? formatDateMMDDYYYY(new Date(microagent.created_at))
    : "";

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

  const cardTitle = microagent?.name ?? conversation?.title;

  const isCardSelected = useMemo(() => {
    if (microagent && selectedMicroagentItem?.microagent) {
      return selectedMicroagentItem.microagent.name === microagent.name;
    }
    if (conversation && selectedMicroagentItem?.conversation) {
      return (
        selectedMicroagentItem.conversation.conversation_id ===
        conversation.conversation_id
      );
    }
    return false;
  }, [microagent, conversation, selectedMicroagentItem]);

  const onMicroagentCardClicked = () => {
    dispatch(
      setSelectedMicroagentItem(
        microagent
          ? {
              microagent,
              conversation: null,
            }
          : {
              microagent: null,
              conversation,
            },
      ),
    );
    dispatch(setSelectedRepository(repository));
  };

  return (
    <div
      className={cn(
        "rounded-lg bg-[#ffffff0d] border border-[#ffffff33] p-4 cursor-pointer hover:bg-[#ffffff33] hover:border-[#C9B974] transition-all duration-300",
        isCardSelected && "bg-[#ffffff33] border-[#C9B974]",
      )}
      onClick={onMicroagentCardClicked}
    >
      <div className="flex flex-col items-start gap-2">
        {statusText && (
          <div className="px-[6px] py-[2px] text-[11px] font-medium bg-[#C9B97433] text-white rounded-2xl">
            {statusText}
          </div>
        )}
        <div className="text-white text-[16px] font-semibold">{cardTitle}</div>
        {!!microagent && (
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
