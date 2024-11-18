import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";

export const useGitHubUser = (gitHubToken: string | null) => {
  const user = useQuery({
    queryKey: ["user", gitHubToken],
    queryFn: async () => {
      const data = await retrieveGitHubUser(gitHubToken!);
      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve user data");
      }

      return data;
    },
    enabled: !!gitHubToken,
    retry: false,
  });

  React.useEffect(() => {
    if (user.data) {
      posthog.identify(user.data.login, {
        company: user.data.company,
        name: user.data.name,
        email: user.data.email,
        user: user.data.login,
        mode: window.__APP_MODE__ || "oss",
      });
    }
  }, [user.data]);

  return user;
};
