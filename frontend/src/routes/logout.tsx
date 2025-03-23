import React from "react";
import { useTranslation } from "react-i18next";
import { useGitHubAuthUrl } from "#/hooks/use-github-auth-url";
import { useConfig } from "#/hooks/query/use-config";
import { AllHandsLogoButton } from "#/components/shared/buttons/all-hands-logo-button";

export default function LogoutPage() {
  const { t } = useTranslation();
  const config = useConfig();

  const gitHubAuthUrl = useGitHubAuthUrl({
    appMode: config.data?.APP_MODE || null,
    gitHubClientId: config.data?.GITHUB_CLIENT_ID || null,
  });

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-base">
      <div className="flex flex-col items-center gap-8 p-8 rounded-lg bg-neutral-800">
        <AllHandsLogoButton />
        <h1 className="text-2xl font-bold text-neutral-200">
          {t("AUTH$LOGGED_OUT")}
        </h1>
        <div className="flex flex-col gap-4">
          <a
            href={gitHubAuthUrl}
            className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 text-center"
          >
            {t("AUTH$LOG_IN_WITH_GITHUB")}
          </a>
        </div>
      </div>
    </div>
  );
}
