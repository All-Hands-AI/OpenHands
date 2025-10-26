import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import UserService from "#/api/user-service/user-service.api";
import { useShouldShowUserFeatures } from "#/hooks/use-should-show-user-features";

export const useGitUser = () => {
  const { data: config } = useConfig();

  // Use the shared hook to determine if we should fetch user data
  const shouldFetchUser = useShouldShowUserFeatures();

  const user = useQuery({
    queryKey: ["user"],
    queryFn: UserService.getUser,
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
