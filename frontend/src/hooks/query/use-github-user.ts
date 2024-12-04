import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";

export const useGitHubUser = () => {
  const { gitHubToken, refreshToken, logout } = useAuth();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", gitHubToken],
    queryFn: async () => {
      const data = await retrieveGitHubUser(gitHubToken!, refreshToken, logout);

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
