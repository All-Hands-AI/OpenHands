import { useQuery } from "@tanstack/react-query";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";
import {
  isGitHubErrorReponse,
  retrieveGitHubAppInstallations,
} from "#/api/github";

export const useAppInstallations = () => {
  const { data: config } = useConfig();
  const { gitHubToken } = useAuth();

  return useQuery({
    queryKey: ["installations", gitHubToken, config?.GITHUB_CLIENT_ID],
    queryFn: async () => {
      const data = await retrieveGitHubAppInstallations();
      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve latest commit");
      }

      return data;
    },
    enabled: !!gitHubToken && !!config?.GITHUB_CLIENT_ID,
  });
};
