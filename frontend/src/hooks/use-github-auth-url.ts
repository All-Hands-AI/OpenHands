import React from "react";
import { generateGitHubAuthUrl } from "#/utils/generate-github-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";

interface UseGitHubAuthUrlConfig {
  gitHubToken: string | null;
  appMode: GetConfigResponse["APP_MODE"] | null;
  gitHubClientId: GetConfigResponse["GITHUB_CLIENT_ID"] | null;
}

export const useGitHubAuthUrl = (config: UseGitHubAuthUrlConfig) =>
  React.useMemo(() => {
    if (config.appMode === "saas" && !config.gitHubToken)
      return generateGitHubAuthUrl(
        config.gitHubClientId || "",
        new URL(window.location.href),
      );

    return null;
  }, [config.gitHubToken, config.appMode, config.gitHubClientId]);
