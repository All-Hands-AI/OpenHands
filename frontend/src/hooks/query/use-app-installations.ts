import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useSettings } from "./use-settings";

export const useAppInstallations = () => {
  const { data: config } = useConfig();
  const { data: settings } = useSettings();

  return useQuery({
    queryKey: [
      "installations",
      settings?.GITHUB_TOKEN_IS_SET,
      config?.GITHUB_CLIENT_ID,
    ],
    queryFn: OpenHands.getGitHubUserInstallationIds,
    enabled:
      !!settings?.GITHUB_TOKEN_IS_SET &&
      !!config?.GITHUB_CLIENT_ID &&
      config?.APP_MODE === "saas",
  });
};
