import { useQuery } from "@tanstack/react-query";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";

export const useAppInstallations = () => {
  const { data: config } = useConfig();
  const { gitHubToken } = useAuth();

  return useQuery({
    queryKey: ["installations", gitHubToken, config?.GITHUB_CLIENT_ID],
    queryFn: OpenHands.getGitHubUserInstallationIds,
    enabled:
      !!gitHubToken &&
      !!config?.GITHUB_CLIENT_ID &&
      config?.APP_MODE === "saas",
  });
};
