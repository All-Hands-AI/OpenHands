import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import BaseModal from "../base-modal/BaseModal";
import Session from "#/services/session";

interface LoadPreviousSessionModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function LoadPreviousSessionModal({
  isOpen,
  onOpenChange,
}: LoadPreviousSessionModalProps) {
  const { t } = useTranslation();

  return (
    <BaseModal
      isOpen={isOpen}
      title={t(I18nKey.LOAD_SESSION$MODAL_TITLE)}
      onOpenChange={onOpenChange}
      isDismissable={false} // prevent unnecessary messages from being stored (issue #1285)
      actions={[
        {
          label: t(I18nKey.LOAD_SESSION$RESUME_SESSION_MODAL_ACTION_LABEL),
          className: "bg-primary rounded-lg",
          action: Session.restoreOrStartNewSession,
          closeAfterAction: true,
        },
        {
          label: t(I18nKey.LOAD_SESSION$START_NEW_SESSION_MODAL_ACTION_LABEL),
          className: "bg-neutral-500 rounded-lg",
          action: Session.startNewSession,
          closeAfterAction: true,
        },
      ]}
    >
      <p>{t(I18nKey.LOAD_SESSION$MODAL_CONTENT)}</p>
    </BaseModal>
  );
}

export default LoadPreviousSessionModal;
