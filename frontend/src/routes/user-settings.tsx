import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useSettings } from "#/hooks/query/use-settings";
import { openHands } from "#/api/open-hands-axios";

function UserSettingsScreen() {
  const { t } = useTranslation();
  const { data: settings, isLoading, refetch } = useSettings();
  const [email, setEmail] = useState("");
  const [originalEmail, setOriginalEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isResendingVerification, setIsResendingVerification] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const queryClient = useQueryClient();
  const pollingIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (settings?.EMAIL) {
      setEmail(settings.EMAIL);
      setOriginalEmail(settings.EMAIL);
    }
  }, [settings?.EMAIL]);

  // Track previous verification status to detect changes
  const prevVerificationStatusRef = useRef<boolean | undefined>(undefined);

  // Set up polling for email verification status when email is not verified
  useEffect(() => {
    // Clear any existing interval
    if (pollingIntervalRef.current) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // Check if verification status changed from false to true
    if (
      prevVerificationStatusRef.current === false &&
      settings?.EMAIL_VERIFIED === true
    ) {
      // Show success message when email is verified
      setSaveSuccess(true);
      setResendSuccess(false); // Hide any resend success message
      setTimeout(() => {
        // Redirect will happen automatically via EmailVerificationGuard
        queryClient.invalidateQueries({ queryKey: ["settings"] });
      }, 2000);
    }

    // Update previous verification status reference
    prevVerificationStatusRef.current = settings?.EMAIL_VERIFIED;

    // Only start polling if email is not verified
    if (settings?.EMAIL_VERIFIED === false) {
      // Check for email verification every 5 seconds
      pollingIntervalRef.current = window.setInterval(() => {
        // Refetch settings to check if email has been verified
        refetch();
      }, 5000);
    }

    // Clean up interval on unmount or when email becomes verified
    return () => {
      if (pollingIntervalRef.current) {
        window.clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [settings?.EMAIL_VERIFIED, refetch, queryClient]);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setSaveSuccess(false);
  };

  const handleSaveEmail = async () => {
    if (email === originalEmail) return;

    try {
      setIsSaving(true);
      await openHands.post(
        "/api/email",
        {
          email,
        },
        {
          withCredentials: true, // Allow cookies to be set from the response
        },
      );

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

      await openHands.put(
        "/api/email/verify",
        {},
        {
          withCredentials: true, // Allow cookies to be set from the response
        },
      );

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
              </div>

              <div className="flex items-center gap-3 mt-2">
                <button
                  type="button"
                  onClick={handleSaveEmail}
                  disabled={!isEmailChanged || isSaving}
                  className="px-4 py-2 rounded bg-primary text-white hover:opacity-80 disabled:opacity-30 disabled:cursor-not-allowed disabled:text-[#0D0F11]"
                  data-testid="save-email-button"
                >
                  {isSaving ? t("SETTINGS$SAVING") : t("SETTINGS$SAVE")}
                </button>

                {settings?.EMAIL_VERIFIED === false && (
                  <button
                    type="button"
                    onClick={handleResendVerification}
                    disabled={isResendingVerification}
                    className="px-4 py-2 rounded bg-primary text-white hover:opacity-80 disabled:opacity-30 disabled:cursor-not-allowed disabled:text-[#0D0F11]"
                    data-testid="resend-verification-button"
                  >
                    {isResendingVerification
                      ? t("SETTINGS$SENDING")
                      : t("SETTINGS$RESEND_VERIFICATION")}
                  </button>
                )}
              </div>

              {settings?.EMAIL_VERIFIED === false && (
                <div
                  className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4"
                  role="alert"
                >
                  <p className="font-bold">
                    {t("SETTINGS$EMAIL_VERIFICATION_REQUIRED")}
                  </p>
                  <p className="text-sm">
                    {t("SETTINGS$EMAIL_VERIFICATION_RESTRICTION_MESSAGE")}
                  </p>
                </div>
              )}

              {saveSuccess && (
                <div className="text-sm text-green-500 mt-1">
                  {settings?.EMAIL_VERIFIED === true &&
                  prevVerificationStatusRef.current === false
                    ? t("SETTINGS$EMAIL_VERIFIED_SUCCESSFULLY")
                    : t("SETTINGS$EMAIL_SAVED_SUCCESSFULLY")}
                </div>
              )}

              {resendSuccess && (
                <div className="text-sm text-green-500 mt-1">
                  {t("SETTINGS$VERIFICATION_EMAIL_SENT")}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserSettingsScreen;
