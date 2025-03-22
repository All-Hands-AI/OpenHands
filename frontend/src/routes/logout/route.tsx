import React from "react";
import { useTranslation } from "react-i18next";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useConfig } from "#/hooks/query/use-config";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useNavigate } from "react-router";
import { BrandButton } from "#/components/features/settings/brand-button";

export default function LogoutPage() {
  const { t } = useTranslation();
  const config = useConfig();
  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  const handleLogin = () => {
    if (gitHubAuthUrl) {
      window.location.href = gitHubAuthUrl;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6 bg-base">
      <h1 className="text-2xl font-semibold">
        {t("LOGOUT$TITLE")}
      </h1>
      <p className="text-base text-[#A3A3A3]">
        {t("LOGOUT$DESCRIPTION")}
      </p>
      <BrandButton
        testId="login-button"
        type="button"
        variant="primary"
        onClick={handleLogin}
      >
        {t("LOGOUT$LOGIN_BUTTON")}
      </BrandButton>
    </div>
  );
}