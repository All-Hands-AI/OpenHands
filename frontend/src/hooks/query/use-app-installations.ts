import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

export const useAppInstallations = () => {
  const { data: config } = useConfig();
  const { providersAreSet } = useAuth();

  return useQuery({
    queryKey: ["installations", providersAreSet, config?.GITHUB_CLIENT_ID],
    queryFn: OpenHands.getGitHubUserInstallationIds,
    enabled:
      providersAreSet &&
      !!config?.GITHUB_CLIENT_ID &&
      config?.APP_MODE === "saas",
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
