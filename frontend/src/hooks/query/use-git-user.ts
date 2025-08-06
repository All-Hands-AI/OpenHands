import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useUserProviders } from "#/hooks/use-user-providers";

export const useGitUser = () => {
  const { data: config } = useConfig();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();

  // Only enable the query if:
  // - We have a valid APP_MODE and user is authenticated, AND
  // - Either we're not in OSS mode OR we have provider tokens configured
  const shouldFetchUser = React.useMemo(() => {
    if (!config?.APP_MODE || !isAuthed) return false;

    // In OSS mode, only fetch user info if Git providers are configured
    if (config.APP_MODE === "oss") {
      return providers.length > 0;
    }

    // In non-OSS modes (saas), always fetch user info when authenticated
    return true;
  }, [config?.APP_MODE, isAuthed, providers.length]);

  const user = useQuery({
    queryKey: ["user"],
    queryFn: OpenHands.getGitUser,
    enabled: shouldFetchUser,
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
