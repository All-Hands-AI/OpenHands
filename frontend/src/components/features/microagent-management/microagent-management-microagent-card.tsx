import { useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
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
  repository: GitRepository;
}

export function MicroagentManagementMicroagentCard({
  microagent,
  conversation,
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

  const hasPr = !!(prNumber && prNumber.length > 0);

  // Helper function to get status text
  const statusText = useMemo(() => {
    if (hasPr) {
      return t(I18nKey.COMMON$READY_FOR_REVIEW);
    }
    if (
      conversationStatus === "STARTING" ||
      runtimeStatus === "STATUS$STARTING_RUNTIME"
    ) {
      return t(I18nKey.COMMON$STARTING);
    }
    if (
      conversationStatus === "STOPPED" ||
      runtimeStatus === "STATUS$STOPPED"
    ) {
      return t(I18nKey.COMMON$STOPPED);
    }
    if (runtimeStatus === "STATUS$ERROR") {
      return t(I18nKey.MICROAGENT$STATUS_ERROR);
    }
    if (conversationStatus === "RUNNING" && runtimeStatus === "STATUS$READY") {
      return t(I18nKey.MICROAGENT$STATUS_OPENING_PR);
    }
    return "";
  }, [conversationStatus, runtimeStatus, t, hasPr]);

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
            {microagent.path}
          </div>
        )}
      </div>
    </div>
  );
}
