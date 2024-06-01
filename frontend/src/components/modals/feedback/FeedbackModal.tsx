import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import BaseModal from "../base-modal/BaseModal";
import { Feedback, sendFeedback } from "#/services/feedbackService";

interface FeedbackModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function FeedbackModal({
  isOpen,
  onOpenChange,
}: FeedbackModalProps) {
  const { t } = useTranslation();

  const [feedback, setFeedback] = React.useState<Feedback>({} as Feedback);
  const [responseCode, setResponseCode] = React.useState<number | null>(null);
  const [responseText, setResponseText] = React.useState<string | null>(null);
  const [responseLoading, setResponseLoading] = React.useState(false);

  const handleSendFeedback = () => {
    setResponseLoading(true);
    sendFeedback(feedback).then(response => {
      setResponseCode(response.status);
      setResponseText(response.statusText);
    }).catch(error => {
      setResponseCode(error.status);
      setResponseText(error.statusText);
    });
    setResponseLoading(false);
  }

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
    </BaseModal>
  );
}

export default FeedbackModal;
