import { Input, useDisclosure } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import { AvailableLanguages } from "../../../i18n";
import { I18nKey } from "../../../i18n/declaration";
import { Feedback } from "#/services/settings";

interface FeedbackFormProps {
  settings: Feedback;
  models: string[];
  agents: string[];
  disabled: boolean;

  onModelChange: (model: string) => void;
  onEmailChange: (email: string) => void;
  onAgentChange: (agent: string) => void;
  onLanguageChange: (language: string) => void;
}

function FeedbackForm({
  feedback,
  onEmailChange,
  onPermissionsChange,
}: FeedbackFormProps) {
  const { t } = useTranslation();
  const { isOpen: isVisible, onOpenChange: onVisibleChange } = useDisclosure();

  const isEmailValid = (email: string) => {
    // Regular expression to validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  return (
    <>
      <Input
        label="Email"
        aria-label="email"
        data-testid="email"
        placeholder={t(I18nKey.FEEDBACK$EMAIL_PLACEHOLDER)}
        type="text"
        value={feedback.email || ""}
        onChange={(e) => {
          onEmailChange(e.target.value);
        }}
      />
      <Input
        label="Sharing settings"
        aria-label="permissions"
        data-testid="permissions"
        type="dropdown"
        value={feedback.permissions}
        onChange={(e) => {
          onPermissionsChange(e.target.value);
        }}
      >
        <option value="public">Public</option>
        <option value="private">Private</option>
      </Input>
      {isEmailValid(feedback.email) ? null : (
        <p className="text-red-500">Invalid email format</p>
      )}
    </>
  );
}

export default FeedbackForm;
