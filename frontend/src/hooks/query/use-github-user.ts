import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useSettings } from "./use-settings";

export const useGitHubUser = () => {
  const { data: settings } = useSettings();
  const { setUserId } = useAuth();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user", settings?.GITHUB_TOKEN_IS_SET],
    queryFn: OpenHands.getGitHubUser,
    enabled: !!settings?.GITHUB_TOKEN_IS_SET && !!config?.APP_MODE,
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
