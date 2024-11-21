import { useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";
import { useConfig } from "./use-config";

interface UseGitHubUserConfig {
  gitHubToken: string | null;
}

export const useGitHubUser = (config: UseGitHubUserConfig) => {
  const queryClient = useQueryClient();
  // Ensure that the app mode is available before fetching user data
  const appMode = queryClient.getQueryData<ReturnType<typeof useConfig>>([
    "config",
  ])?.data?.APP_MODE;

  const user = useQuery({
    queryKey: ["user", config.gitHubToken],
    queryFn: async () => {
      const data = await retrieveGitHubUser(config.gitHubToken!);

      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve user data");
      }

      return data;
    },
    enabled: !!config.gitHubToken && !!appMode,
    retry: false,
  });

  React.useEffect(() => {
    if (user.data) {
      posthog.identify(user.data.login, {
        company: user.data.company,
        name: user.data.name,
        email: user.data.email,
        user: user.data.login,
        mode: appMode || "oss",
      });
    }
  }, [user.data]);

  return user;
};
