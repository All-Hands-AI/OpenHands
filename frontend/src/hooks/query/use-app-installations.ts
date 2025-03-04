import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

export const useAppInstallations = () => {
  const { data: config } = useConfig();
  const { tokenIsSet } = useAuth();

  return useQuery({
    queryKey: ["installations", tokenIsSet, config?.GITHUB_CLIENT_ID],
    queryFn: OpenHands.getGitHubUserInstallationIds,
    enabled:
      tokenIsSet && !!config?.GITHUB_CLIENT_ID && config?.APP_MODE === "saas",
  });
};
