import { useAuthUrl } from "./use-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";

interface UseGitHubAuthUrlConfig {
  appMode: GetConfigResponse["APP_MODE"] | null;
  gitHubClientId: GetConfigResponse["GITHUB_CLIENT_ID"] | null;
}

export const useGitHubAuthUrl = (config: UseGitHubAuthUrlConfig) =>
  useAuthUrl({
    appMode: config.appMode,
    identityProvider: "github",
  });
