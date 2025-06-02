import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useSettings } from "#/hooks/query/use-settings";
import { openHands } from "#/api/open-hands-axios";

function UserSettingsScreen() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useSettings();
  const [email, setEmail] = useState("");
  const [originalEmail, setOriginalEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isResendingVerification, setIsResendingVerification] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (settings?.EMAIL) {
      setEmail(settings.EMAIL);
      setOriginalEmail(settings.EMAIL);
    }
  }, [settings?.EMAIL]);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setSaveSuccess(false);
  };

  const handleSaveEmail = async () => {
    if (email === originalEmail) return;

    try {
      setIsSaving(true);
      await openHands.post("/api/email", {
        email,
      });

      setOriginalEmail(email);
      setSaveSuccess(true);

      // Invalidate settings query to refresh data
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    } catch (error) {
      // Log error but don't show to user
      // eslint-disable-next-line no-console
      console.error(t("SETTINGS$FAILED_TO_SAVE_EMAIL"), error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleResendVerification = async () => {
    try {
      setIsResendingVerification(true);
      setResendSuccess(false);
      
      await openHands.put("/api/email/verify");
      
      setResendSuccess(true);
    } catch (error) {
      // Log error but don't show to user
      // eslint-disable-next-line no-console
      console.error(t("SETTINGS$FAILED_TO_RESEND_VERIFICATION"), error);
    } finally {
      setIsResendingVerification(false);
    }
  };

  const isEmailChanged = email !== originalEmail;

  return (
    <div data-testid="user-settings-screen" className="flex flex-col h-full">
      <div className="p-9 flex flex-col gap-6">
        {isLoading ? (
          <div className="animate-pulse h-8 w-64 bg-tertiary rounded" />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm">{t("SETTINGS$USER_EMAIL")}</label>
              <div className="flex items-center gap-3">
                <input
                  type="email"
                  value={email}
                  onChange={handleEmailChange}
                  className="text-base text-primary p-2 bg-base-tertiary rounded border border-tertiary flex-grow"
                  placeholder={t("SETTINGS$USER_EMAIL_NOT_AVAILABLE")}
                  data-testid="email-input"
                />
                <button
                  type="button"
                  onClick={handleSaveEmail}
                  disabled={!isEmailChanged || isSaving}
                  className={`px-4 py-2 rounded ${
                    isEmailChanged && !isSaving
                      ? "bg-primary text-white hover:bg-primary-dark"
                      : "bg-tertiary text-secondary cursor-not-allowed"
                  }`}
                  data-testid="save-email-button"
                >
                  {isSaving ? t("SETTINGS$SAVING") : t("SETTINGS$SAVE")}
                </button>
              </div>
              {saveSuccess && (
                <div className="text-sm text-green-500 mt-1">
                  {t("SETTINGS$EMAIL_SAVED_SUCCESSFULLY")}
                </div>
              )}
              
              <div className="mt-4">
                <button
                  type="button"
                  onClick={handleResendVerification}
                  disabled={isResendingVerification}
                  className={`px-4 py-2 rounded ${
                    !isResendingVerification
                      ? "bg-primary text-white hover:bg-primary-dark"
                      : "bg-tertiary text-secondary cursor-not-allowed"
                  }`}
                  data-testid="resend-verification-button"
                >
                  {isResendingVerification ? t("SETTINGS$SENDING") : "Resend verification"}
                </button>
                {resendSuccess && (
                  <div className="text-sm text-green-500 mt-1">
                    {t("SETTINGS$VERIFICATION_EMAIL_SENT")}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserSettingsScreen;
