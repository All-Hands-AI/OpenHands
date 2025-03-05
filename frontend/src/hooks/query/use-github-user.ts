import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useCurrentSettings } from "#/context/settings-context";

export const useGitHubUser = () => {
  const { logout } = useAuth();
  const { saveUserSettings, settings } = useCurrentSettings();
  const { data: config } = useConfig();

  const hasGitHubTokenSet = !!settings?.GITHUB_TOKEN_IS_SET;

  const user = useQuery({
    queryKey: ["user", hasGitHubTokenSet],
    queryFn: OpenHands.getGitHubUser,
    enabled: hasGitHubTokenSet && !!config?.APP_MODE,
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

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") logout();
    else {
      await saveUserSettings({ unset_github_token: true });
    }
    posthog.reset();
  };

  React.useEffect(() => {
    if (user.isError) {
      handleLogout();
    }
  }, [user.isError]);

  return user;
};
