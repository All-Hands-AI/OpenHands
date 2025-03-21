import React from "react";
import { generateGitHubAuthUrl } from "#/utils/generate-github-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";
import { useAuth } from "#/context/auth-context";

interface UseGitHubAuthUrlConfig {
  appMode: GetConfigResponse["APP_MODE"] | null;
  gitHubClientId: GetConfigResponse["GITHUB_CLIENT_ID"] | null;
}

export const useGitHubAuthUrl = (config: UseGitHubAuthUrlConfig) => {
  const { providersAreSet } = useAuth();

  return React.useMemo(() => {
    if (config.appMode === "saas" && !providersAreSet)
      return generateGitHubAuthUrl(
        config.gitHubClientId || "",
        new URL(window.location.href),
      );

    return null;
  }, [providersAreSet, config.appMode, config.gitHubClientId]);
};
