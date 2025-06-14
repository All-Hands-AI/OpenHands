import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useUserProviders } from "../use-user-providers";

export const useGitUser = () => {
  const { providers } = useUserProviders();
  const { data: config } = useConfig();

  const user = useQuery({
    queryKey: ["user"],
    queryFn: OpenHands.getGitUser,
    enabled: !!config?.APP_MODE && providers.length > 0,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
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
