import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useConfig } from "./use-config";
import UserService from "#/api/user-service/user-service.api";
import { useShouldShowUserFeatures } from "#/hooks/use-should-show-user-features";
import { useKeycloakId } from "./use-keycloak-id";

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

  // Fetch Keycloak user ID for aliasing (SaaS only)
  const { data: keycloakId } = useKeycloakId();

  React.useEffect(() => {
    if (user.data) {
      // Identify user with GitHub username (primary identifier)
      posthog.identify(user.data.login, {
        company: user.data.company,
        name: user.data.name,
        email: user.data.email,
        user: user.data.login,
        mode: config?.APP_MODE || "oss",
      });

      // If we have both GitHub username and Keycloak ID, alias them
      // PostHog alias syntax: alias(alias_id, original_id)
      // We're aliasing the Keycloak ID (old) to the GitHub username (new/primary)
      if (keycloakId && config?.APP_MODE === "saas") {
        posthog.alias(keycloakId, user.data.login);
      }
    }
  }, [user.data, keycloakId, config?.APP_MODE]);

  return user;
};
