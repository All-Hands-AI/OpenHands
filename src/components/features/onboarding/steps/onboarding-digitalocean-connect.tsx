import React from "react";
import { useTranslation } from "react-i18next";
import DigitalOceanLogo from "#/assets/branding/digitalocean-logo.svg?react";
import {
  getMarsWebBridgeAuthRequired,
  resolveMarsWebBridgeAuth,
  saveHostingSessionKey,
  type MarsWebBridgeError,
} from "#/api/mars/mars-web-bridge";
import { DigitalOceanConnectPanel } from "#/components/features/backends/managed-agents/digitalocean-connect-panel";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { BrandButton } from "#/components/features/settings/brand-button";
import { BackNavButton } from "#/components/shared/buttons/back-nav-button";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

interface OnboardingDigitalOceanConnectProps {
  onBack: () => void;
  onConnected: () => void;
}

/**
 * The DigitalOcean provider view inside first-run onboarding.
 *
 * On a keyed non-loopback / no-baked-key host the provider bridge is mounted
 * but the page has no hosting session key to present, so any `/mars/rpc/*`
 * call (including sign-in and the DO token submit) would 401 with
 * "session key required". Before surfacing the DO sign-in this component
 * collects the hosting key first, in the same explicit manner as the rest of
 * the app, validates it against the bridge, and stores it through the backend
 * registry (backend#18434). It never shows the DO token form while that
 * hosting key is missing, and never copies the host key into the guest
 * backend's `apiKey`.
 */
export function OnboardingDigitalOceanConnect({
  onBack,
  onConnected,
}: OnboardingDigitalOceanConnectProps) {
  const { t } = useTranslation("openhands");
  const hostingAuthRequired = getMarsWebBridgeAuthRequired();
  const auth = resolveMarsWebBridgeAuth(hostingAuthRequired);
  const [hostingKey, setHostingKey] = React.useState("");
  const [isChecking, setIsChecking] = React.useState(false);
  const [hostingError, setHostingError] = React.useState<string | null>(null);
  const [hostingOk, setHostingOk] = React.useState(!auth.missing);

  const submitHostingKey = React.useCallback(async () => {
    if (!hostingKey.trim()) {
      setHostingError(t(I18nKey.AUTH$INVALID_KEY));
      return;
    }
    setIsChecking(true);
    setHostingError(null);
    try {
      await saveHostingSessionKey(hostingKey.trim());
      setHostingOk(true);
    } catch (error) {
      const marsError = error as MarsWebBridgeError;
      setHostingError(
        marsError?.message === "session key required"
          ? t(I18nKey.AUTH$INVALID_KEY)
          : t(I18nKey.AUTH$CONNECTION_FAILED),
      );
    } finally {
      setIsChecking(false);
    }
  }, [hostingKey, t]);

  if (!hostingOk) {
    return (
      <div className="flex flex-col gap-4">
        <BackNavButton onClick={onBack} testId="onboarding-digitalocean-back">
          {t(I18nKey.BUTTON$BACK)}
        </BackNavButton>
        <div className="flex min-w-0 items-center gap-3">
          <span
            className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-surface-raised"
            aria-hidden
          >
            <DigitalOceanLogo width={32} height={32} />
          </span>
          <h2 className="text-xl font-medium text-contrast">
            {t(I18nKey.DO_AGENTS$HOSTING_AUTH_TITLE)}
          </h2>
        </div>
        <p
          className="text-sm text-muted"
          data-testid="onboarding-digitalocean-hosting-auth-hint"
        >
          {t(I18nKey.DO_AGENTS$HOSTING_AUTH_HINT)}
        </p>
        <SettingsInput
          testId="onboarding-digitalocean-hosting-key"
          type="password"
          label={t(I18nKey.BACKEND$KEY_LABEL)}
          value={hostingKey}
          onChange={(v) => {
            setHostingKey(v);
            setHostingError(null);
          }}
          className="w-full"
        />
        {hostingError ? (
          <div
            role="alert"
            data-testid="onboarding-digitalocean-hosting-error"
            className={cn(
              "rounded-md border border-semantic-danger/40 bg-semantic-danger/5 p-3 text-sm text-feedback-error whitespace-pre-wrap break-words",
            )}
          >
            {hostingError}
          </div>
        ) : null}
        <BrandButton
          type="button"
          variant="primary"
          isDisabled={!hostingKey.trim() || isChecking}
          onClick={() => void submitHostingKey()}
          testId="onboarding-digitalocean-hosting-submit"
          className="w-full text-center"
        >
          {t(I18nKey.BACKEND$CONNECT)}
        </BrandButton>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <BackNavButton onClick={onBack} testId="onboarding-digitalocean-back">
        {t(I18nKey.BUTTON$BACK)}
      </BackNavButton>
      <div className="flex min-w-0 items-center gap-3">
        <span
          className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-surface-raised"
          aria-hidden
        >
          <DigitalOceanLogo width={32} height={32} />
        </span>
        <h2 className="text-xl font-medium text-contrast">
          {t(I18nKey.DO_AGENTS$BADGE)}
        </h2>
      </div>
      <DigitalOceanConnectPanel onConnected={onConnected} />
    </div>
  );
}
