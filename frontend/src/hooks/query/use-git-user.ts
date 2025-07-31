import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useIsAuthed } from "#/hooks/query/use-is-authed";

export const useGitUser = () => {
  const { data: config } = useConfig();
  const { data: isAuthed } = useIsAuthed();

  const user = useQuery({
    queryKey: ["user"],
    queryFn: OpenHands.getGitUser,
    enabled: !!config?.APP_MODE && isAuthed === true, // Enable regardless of providers
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
