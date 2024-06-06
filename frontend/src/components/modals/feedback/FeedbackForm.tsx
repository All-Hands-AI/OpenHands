import { Input, Select, SelectItem } from "@nextui-org/react";
import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "../../../i18n/declaration";
import { Feedback } from "#/services/feedbackService";

interface FeedbackFormProps {
  feedback: Feedback;

  onEmailChange: (email: string) => void;
  onPermissionsChange: (permissions: "public" | "private") => void;
}

function FeedbackForm({
  feedback,
  onEmailChange,
  onPermissionsChange,
}: FeedbackFormProps) {
  const { t } = useTranslation();

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
      <Select
        label="Sharing settings"
        aria-label="permissions"
        data-testid="permissions"
        value={feedback.permissions}
        onChange={(e) => {
          onPermissionsChange(e.target.value as "public" | "private");
        }}
      >
        <SelectItem key="public" value="public">
          Public
        </SelectItem>
        <SelectItem key="private" value="private">
          Private
        </SelectItem>
      </Select>
      {isEmailValid(feedback.email) ? null : (
        <p className="text-red-500">Invalid email format</p>
      )}
    </>
  );
}

export default FeedbackForm;
