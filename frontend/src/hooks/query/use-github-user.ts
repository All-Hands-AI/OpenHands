import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useLogout } from "../mutation/use-logout";

export const useGitHubUser = () => {
  const { githubTokenIsSet } = useAuth();
  const { mutate: logout } = useLogout();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", githubTokenIsSet],
    queryFn: OpenHands.getGitHubUser,
    enabled: githubTokenIsSet && !!config?.APP_MODE,
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

  React.useEffect(() => {
    if (user.isError) {
      logout();
    }
  }, [user.isError]);

  return user;
};
