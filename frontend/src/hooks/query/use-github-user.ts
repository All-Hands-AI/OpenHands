import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { retrieveGitHubUser } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";

export const useGitHubUser = () => {
  const { gitHubToken, setUserId } = useAuth();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", gitHubToken],
    queryFn: retrieveGitHubUser,
    enabled: !!gitHubToken && !!config?.APP_MODE,
    retry: false,
  });

  React.useEffect(() => {
    if (user.data) {
      setUserId(user.data.id.toString());
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
