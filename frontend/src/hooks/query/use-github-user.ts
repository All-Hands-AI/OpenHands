import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useLogout } from "../mutation/use-logout";
import { useCurrentSettings } from "#/context/settings-context";

export const useGitHubUser = () => {
  const { githubTokenIsSet } = useAuth();
  const { setGitHubTokenIsSet } = useAuth();
  const { mutateAsync: logout } = useLogout();
  const { saveUserSettings } = useCurrentSettings();
  const { data: config } = useConfig();

  const query = useQuery({
    queryKey: ["user", githubTokenIsSet],
    queryFn: OpenHands.getGitHubUser,
    enabled: githubTokenIsSet && !!config?.APP_MODE,
    retry: false,
  });

  React.useEffect(() => {
    const { data } = query
    if (data) {
      posthog.identify(data.login, {
        company: data.company,
        name: data.name,
        email: data.email,
        user: data.login,
        mode: config?.APP_MODE || "oss",
      });
    }
  }, [query.data]);

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") await logout();
    else {
      await saveUserSettings({ unset_github_token: true });
      setGitHubTokenIsSet(false);
    }
    posthog.reset();
  };

  React.useEffect(() => {
    if (query.isError) {
      handleLogout();
    }
  }, [query.isError]);

  return { user: query.data, isLoading: query.isLoading || query.isPending};
};
