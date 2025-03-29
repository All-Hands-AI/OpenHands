import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useLogout } from "../mutation/use-logout";

export const useGitHubUser = () => {
  const { githubTokenIsSet } = useAuth();
  const { mutateAsync: logout } = useLogout();

  const { data: config } = useConfig();

  // Add logging to debug the hook's behavior
  console.log("[useGitHubUser] Hook initialized", {
    githubTokenIsSet,
    appMode: config?.APP_MODE,
    enabled: githubTokenIsSet && !!config?.APP_MODE,
  });

  const user = useQuery({
    queryKey: ["user", githubTokenIsSet],
    queryFn: async () => {
      console.log("[useGitHubUser] Fetching GitHub user data");
      try {
        const userData = await OpenHands.getGitHubUser();
        console.log("[useGitHubUser] GitHub user data fetched successfully", userData);
        return userData;
      } catch (error) {
        console.error("[useGitHubUser] Error fetching GitHub user data:", error);
        throw error;
      }
    },
    enabled: githubTokenIsSet && !!config?.APP_MODE,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  // Log query state changes
  React.useEffect(() => {
    console.log("[useGitHubUser] Query state updated", {
      isLoading: user.isLoading,
      isError: user.isError,
      error: user.error,
      data: user.data,
    });
  }, [user.isLoading, user.isError, user.error, user.data]);

  React.useEffect(() => {
    if (user.data) {
      console.log("[useGitHubUser] User data available, identifying in posthog");
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
    console.log("[useGitHubUser] Handling logout due to error");
    await logout();
    posthog.reset();
  };

  React.useEffect(() => {
    if (user.isError) {
      console.error("[useGitHubUser] Error detected, logging out", user.error);
      handleLogout();
    }
  }, [user.isError]);

  return user;
};
