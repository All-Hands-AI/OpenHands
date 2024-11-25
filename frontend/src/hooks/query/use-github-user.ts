import { useQuery } from "@tanstack/react-query";
import React from "react";
import { usePostHog } from "posthog-js/react";
import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";

export const useGitHubUser = () => {
  const posthog = usePostHog();
  const { gitHubToken } = useAuth();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", gitHubToken],
    queryFn: async () => {
      const data = await retrieveGitHubUser(gitHubToken!);

      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve user data");
      }

      return data;
    },
    enabled: !!gitHubToken && !!config?.APP_MODE,
    retry: false,
  });

  React.useEffect(() => {
    if (user.data) {
      posthog.identify(user.data.login, {
        company: user.data.company,
        name: user.data.name,
        email: user.data.email,
        user: user.data.login,
        mode: config?.APP_MODE || "oss",
      });
    }
  }, [user.data]);

  return user;
};
