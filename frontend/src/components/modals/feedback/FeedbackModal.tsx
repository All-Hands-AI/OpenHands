import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import BaseModal from "../base-modal/BaseModal";
import { Feedback, sendFeedback } from "#/services/feedbackService";
import FeedbackForm from "./FeedbackForm";
import toast from "#/utils/toast";

interface FeedbackModalProps {
  feedback: Feedback;
  handleEmailChange: (key: string) => void;
  handlePermissionsChange: (permissions: "public" | "private") => void;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function FeedbackModal({
  feedback,
  handleEmailChange,
  handlePermissionsChange,
  isOpen,
  onOpenChange,
}: FeedbackModalProps) {
  const { t } = useTranslation();

  const handleSendFeedback = () => {
    sendFeedback(feedback)
      .then((response) => {
        if (response.message === "Feedback submitted successfully") {
          toast.info(response.message);
        } else {
          toast.error(
            "share-error",
            `Failed to share, please contact the developers: ${response.message}`,
          );
        }
      })
      .catch((error) => {
        toast.error(
          "share-error",
          `Failed to share, please contact the developers: ${error}`,
        );
      });
  };

  return (
    <BaseModal
      isOpen={isOpen}
      title={t(I18nKey.FEEDBACK$MODAL_TITLE)}
      onOpenChange={onOpenChange}
      isDismissable={false} // prevent unnecessary messages from being stored (issue #1285)
      actions={[
        {
          label: t(I18nKey.FEEDBACK$SHARE_LABEL),
          className: "bg-primary rounded-lg",
          action: handleSendFeedback,
          closeAfterAction: true,
        },
        {
          label: t(I18nKey.FEEDBACK$CANCEL_LABEL),
          className: "bg-neutral-500 rounded-lg",
          action() {},
          closeAfterAction: true,
        },
      ]}
    >
      <p>{t(I18nKey.FEEDBACK$MODAL_CONTENT)}</p>
      <FeedbackForm
        feedback={feedback}
        onEmailChange={handleEmailChange}
        onPermissionsChange={handlePermissionsChange}
      />
    </BaseModal>
  );
}

export default FeedbackModal;
