import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useLogout } from "../mutation/use-logout";
import { useCurrentSettings } from "#/context/settings-context";

export const useGitHubUser = () => {
  const { providersAreSet } = useAuth();
  const { setProvidersAreSet } = useAuth();
  const { mutateAsync: logout } = useLogout();
  const { saveUserSettings } = useCurrentSettings();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", providersAreSet],
    queryFn: OpenHands.getGitHubUser,
    enabled: providersAreSet && !!config?.APP_MODE,
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
    if (config?.APP_MODE === "saas") await logout();
    else {
      await saveUserSettings({ unset_tokens: true });
      setProvidersAreSet(false);
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
