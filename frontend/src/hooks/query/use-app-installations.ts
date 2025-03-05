import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

export const useAppInstallations = () => {
  const { data: config } = useConfig();
  const { githubTokenIsSet } = useAuth();

  return useQuery({
    queryKey: ["installations", githubTokenIsSet, config?.GITHUB_CLIENT_ID],
    queryFn: OpenHands.getGitHubUserInstallationIds,
    enabled:
      githubTokenIsSet &&
      !!config?.GITHUB_CLIENT_ID &&
      config?.APP_MODE === "saas",
  });
};
