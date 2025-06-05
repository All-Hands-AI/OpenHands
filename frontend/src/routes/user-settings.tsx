import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useSettings } from "#/hooks/query/use-settings";
import { openHands } from "#/api/open-hands-axios";

function EmailInputSection({
  email,
  onEmailChange,
  onSaveEmail,
  onResendVerification,
  isSaving,
  isResendingVerification,
  isEmailChanged,
  emailVerified,
  children,
}: {
  email: string;
  onEmailChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSaveEmail: () => void;
  onResendVerification: () => void;
  isSaving: boolean;
  isResendingVerification: boolean;
  isEmailChanged: boolean;
  emailVerified?: boolean;
  children: React.ReactNode;
}) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <label className="text-sm">{t("SETTINGS$USER_EMAIL")}</label>
        <div className="flex items-center gap-3">
          <input
            type="email"
            value={email}
            onChange={onEmailChange}
            className="text-base text-white p-2 bg-base-tertiary rounded border border-tertiary flex-grow focus:outline-none focus:border-transparent focus:ring-0"
            placeholder={t("SETTINGS$USER_EMAIL_LOADING")}
            data-testid="email-input"
          />
        </div>

        <div className="flex items-center gap-3 mt-2">
          <button
            type="button"
            onClick={onSaveEmail}
            disabled={!isEmailChanged || isSaving}
            className="px-4 py-2 rounded bg-primary text-white hover:opacity-80 disabled:opacity-30 disabled:cursor-not-allowed disabled:text-[#0D0F11]"
            data-testid="save-email-button"
          >
            {isSaving ? t("SETTINGS$SAVING") : t("SETTINGS$SAVE")}
          </button>

          {emailVerified === false && (
            <button
              type="button"
              onClick={onResendVerification}
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

        {children}
      </div>
    </div>
  );
}

function VerificationAlert() {
  const { t } = useTranslation();
  return (
    <div
      className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4"
      role="alert"
    >
      <p className="font-bold">{t("SETTINGS$EMAIL_VERIFICATION_REQUIRED")}</p>
      <p className="text-sm">
        {t("SETTINGS$EMAIL_VERIFICATION_RESTRICTION_MESSAGE")}
      </p>
    </div>
  );
}

function SaveSuccessMessage({
  emailVerified,
  wasPreviouslyUnverified,
}: {
  emailVerified?: boolean;
  wasPreviouslyUnverified: boolean;
}) {
  const { t } = useTranslation();
  const message =
    emailVerified && wasPreviouslyUnverified
      ? t("SETTINGS$EMAIL_VERIFIED_SUCCESSFULLY")
      : t("SETTINGS$EMAIL_SAVED_SUCCESSFULLY");

  return <div className="text-sm text-green-500 mt-1">{message}</div>;
}

function ResendSuccessMessage() {
  const { t } = useTranslation();
  return (
    <div className="text-sm text-green-500 mt-1">
      {t("SETTINGS$VERIFICATION_EMAIL_SENT")}
    </div>
  );
}

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
  const prevVerificationStatusRef = useRef<boolean | undefined>(undefined);

  useEffect(() => {
    if (settings?.EMAIL) {
      setEmail(settings.EMAIL);
      setOriginalEmail(settings.EMAIL);
    }
  }, [settings?.EMAIL]);

  useEffect(() => {
    if (pollingIntervalRef.current) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    if (
      prevVerificationStatusRef.current === false &&
      settings?.EMAIL_VERIFIED === true
    ) {
      setSaveSuccess(true);
      setResendSuccess(false);
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["settings"] });
      }, 2000);
    }

    prevVerificationStatusRef.current = settings?.EMAIL_VERIFIED;

    if (settings?.EMAIL_VERIFIED === false) {
      pollingIntervalRef.current = window.setInterval(() => {
        refetch();
      }, 5000);
    }

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
      await openHands.post("/api/email", { email }, { withCredentials: true });
      setOriginalEmail(email);
      setSaveSuccess(true);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    } catch (error) {
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
      await openHands.put("/api/email/verify", {}, { withCredentials: true });
      setResendSuccess(true);
    } catch (error) {
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
          <EmailInputSection
            email={email}
            onEmailChange={handleEmailChange}
            onSaveEmail={handleSaveEmail}
            onResendVerification={handleResendVerification}
            isSaving={isSaving}
            isResendingVerification={isResendingVerification}
            isEmailChanged={isEmailChanged}
            emailVerified={settings?.EMAIL_VERIFIED}
          >
            {settings?.EMAIL_VERIFIED === false && <VerificationAlert />}
            {saveSuccess && (
              <SaveSuccessMessage
                emailVerified={settings?.EMAIL_VERIFIED}
                wasPreviouslyUnverified={
                  prevVerificationStatusRef.current === false
                }
              />
            )}
            {resendSuccess && <ResendSuccessMessage />}
          </EmailInputSection>
        )}
      </div>
    </div>
  );
}

export default UserSettingsScreen;
