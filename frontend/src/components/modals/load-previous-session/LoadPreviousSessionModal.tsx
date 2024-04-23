import React from "react";
import { useTranslation } from "react-i18next";
import BaseModal from "../base-modal/BaseModal";
import { clearMsgs, fetchMsgs } from "../../../services/session";
import { sendChatMessageFromEvent } from "../../../services/chatService";
import { handleAssistantMessage } from "../../../services/actions";
import toast from "../../../utils/toast";
import { I18nKey } from "../../../i18n/declaration";

interface LoadPreviousSessionModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function LoadPreviousSessionModal({
  isOpen,
  onOpenChange,
}: LoadPreviousSessionModalProps) {
  const { t } = useTranslation();

  const onStartNewSession = async () => {
    await clearMsgs();
  };

  const onResumeSession = async () => {
    try {
      const { messages } = await fetchMsgs();

      messages.forEach((message) => {
        if (message.role === "user") {
          sendChatMessageFromEvent(message.payload);
        }

        if (message.role === "assistant") {
          handleAssistantMessage(message.payload);
        }
      });
    } catch (error) {
      toast.stickyError("ws", "Error fetching the session");
    }
  };

  return (
    <BaseModal
      isOpen={isOpen}
      title={t(I18nKey.LOAD_SESSION$MODAL_TITLE)}
      onOpenChange={onOpenChange}
      isDismissable={false} // prevent unnecessary messages from being stored (issue #1285)
      actions={[
        {
          label: t(I18nKey.LOAD_SESSION$RESUME_SESSION_MODAL_ACTION_LABEL),
          className: "bg-primary rounded-small",
          action: onResumeSession,
          closeAfterAction: true,
        },
        {
          label: t(I18nKey.LOAD_SESSION$START_NEW_SESSION_MODAL_ACTION_LABEL),
          className: "bg-neutral-500 rounded-small",
          action: onStartNewSession,
          closeAfterAction: true,
        },
      ]}
    >
      <p>{t(I18nKey.LOAD_SESSION$MODAL_CONTENT)}</p>
    </BaseModal>
  );
}

export default LoadPreviousSessionModal;
