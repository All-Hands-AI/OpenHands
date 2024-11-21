import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";
import { GetConfigResponse } from "#/api/open-hands.types";

interface UseGitHubUserConfig {
  gitHubToken: string | null;
  appMode?: GetConfigResponse["APP_MODE"];
}

export const useGitHubUser = (config: UseGitHubUserConfig) => {
  const user = useQuery({
    queryKey: ["user", config.gitHubToken],
    queryFn: async () => {
      const data = await retrieveGitHubUser(config.gitHubToken!);
      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve user data");
      }

      return data;
    },
    enabled: !!config.gitHubToken,
    retry: false,
  });

  React.useEffect(() => {
    if (user.data) {
      posthog.identify(user.data.login, {
        company: user.data.company,
        name: user.data.name,
        email: user.data.email,
        user: user.data.login,
        mode: config.appMode || "oss",
      });
    }
  }, [user.data]);

  return user;
};
