import React from "react";
import { useTranslation } from "react-i18next";
import { Input, Radio, RadioGroup } from "@nextui-org/react";
import { I18nKey } from "#/i18n/declaration";
import BaseModal from "../base-modal/BaseModal";
import { Feedback, sendFeedback } from "#/services/feedbackService";
import toast from "#/utils/toast";
import { getToken } from "#/services/auth";
import Session from "#/services/session";
import { removeApiKey } from "#/utils/utils";

const isEmailValid = (email: string) => {
  // Regular expression to validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const VIEWER_PAGE = "https://www.all-hands.dev/share-opendevin";
const FEEDBACK_VERSION = "1.0";

interface FeedbackModalProps {
  polarity: "positive" | "negative";
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onSendFeedback: () => void;
}

function FeedbackModal({
  polarity,
  isOpen,
  onOpenChange,
  onSendFeedback,
}: FeedbackModalProps) {
  const { t } = useTranslation();

  const [email, setEmail] = React.useState("");
  const [permissions, setPermissions] = React.useState<"public" | "private">(
    "private",
  );

  React.useEffect(() => {
    // check if email is stored in local storage
    const storedEmail = localStorage.getItem("feedback-email");
    if (storedEmail) setEmail(storedEmail);
  }, []);

  const handleEmailChange = (newEmail: string) => {
    setEmail(newEmail);
  };

  const handleSendFeedback = async () => {
    onSendFeedback();
    const feedback: Feedback = {
      version: FEEDBACK_VERSION,
      feedback: polarity,
      email,
      permissions,
      token: getToken(),
      trajectory: removeApiKey(Session._history),
    };

    try {
      const response = await sendFeedback(feedback);
      localStorage.setItem("feedback-email", email); // store email in local storage
      if (response.statusCode === 200) {
        const { message, feedback_id: feedbackId, password } = response.body;
        const toastMessage = `${message}\nFeedback link: ${VIEWER_PAGE}?share_id=${feedbackId}\nPassword: ${password}`;
        toast.info(toastMessage);
      } else {
        toast.error(
          "share-error",
          `Failed to share, please contact the developers: ${response.body.message}`,
        );
      }
    } catch (error) {
      toast.error(
        "share-error",
        `Failed to share, please contact the developers: ${error}`,
      );
    }
  };

  return (
    <BaseModal
      testID="feedback-modal"
      isOpen={isOpen}
      title={t(I18nKey.FEEDBACK$MODAL_TITLE)}
      onOpenChange={onOpenChange}
      isDismissable={false} // prevent unnecessary messages from being stored (issue #1285)
      actions={[
        {
          label: t(I18nKey.FEEDBACK$SHARE_LABEL),
          className: "bg-primary rounded-lg",
          action: handleSendFeedback,
          isDisabled: !isEmailValid(email),
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

      <Input
        label="Email"
        aria-label="email"
        data-testid="email-input"
        placeholder={t(I18nKey.FEEDBACK$EMAIL_PLACEHOLDER)}
        type="text"
        value={email}
        onChange={(e) => {
          handleEmailChange(e.target.value);
        }}
      />
      {!isEmailValid(email) && (
        <p data-testid="invalid-email-message" className="text-red-500">
          Invalid email format
        </p>
      )}
      <RadioGroup
        data-testid="permissions-group"
        label="Sharing settings"
        orientation="horizontal"
        value={permissions}
        onValueChange={(value) => setPermissions(value as "public" | "private")}
      >
        <Radio value="private">{t(I18nKey.FEEDBACK$PRIVATE_LABEL)}</Radio>
        <Radio value="public">{t(I18nKey.FEEDBACK$PUBLIC_LABEL)}</Radio>
      </RadioGroup>
    </BaseModal>
  );
}

export default FeedbackModal;
