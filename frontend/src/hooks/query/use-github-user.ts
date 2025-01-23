import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";

export const useGitHubUser = () => {
  const { gitHubToken, setUserId, logout } = useAuth();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", gitHubToken],
    queryFn: OpenHands.getGitHubUser,
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

  React.useEffect(() => {
    if (user.isError) {
      logout();
    }
  }, [user.isError]);

  return user;
};
