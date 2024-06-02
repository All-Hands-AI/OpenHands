import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import BaseModal from "../base-modal/BaseModal";
import { Feedback, sendFeedback } from "#/services/feedbackService";
import FeedbackForm from "./FeedbackForm";
import toast from "#/utils/toast";

interface FeedbackModalProps {
  feedback: Feedback;
  setFeedback: (feedback: Feedback) => void;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function FeedbackModal({
  feedback,
  setFeedback,
  isOpen,
  onOpenChange,
}: FeedbackModalProps) {
  const { t } = useTranslation();


  const [responseCode, setResponseCode] = React.useState<number | null>(null);
  const [responseText, setResponseText] = React.useState<string | null>(null);
  const [responseLoading, setResponseLoading] = React.useState(false);

  const handleSendFeedback = () => {
    setResponseLoading(true);
    sendFeedback(feedback).then(response => {
      if (response.status === 200) {
        toast.info("Feedback shared successfully.");
      } else {
        toast.error("share-error", "Failed to share, see console for details.");
        console.error(response.status, response.data);
      }
    }).catch(error => {
      toast.error("share-error", "Failed to share, see console for details.");
      console.error(error);
    });
    setResponseLoading(false);
  }

  const handleEmailChange = (key: string) => {
    setFeedback({ ...feedback, email: key } as Feedback);
  };

  const handlePermissionsChange = (permissions: "public" | "private") => {
    setFeedback({ ...feedback, permissions: permissions } as Feedback);
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
          action: function() {},
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
