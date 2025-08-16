import React from "react";
import { useConfig } from "./query/use-config";
import { useIsAuthed } from "./query/use-is-authed";
import { useUserProviders } from "./use-user-providers";
import { getLoginMethod } from "#/utils/local-storage";

/**
 * Hook to determine if user-related features should be shown or enabled
 * based on authentication status and provider configuration.
 *
 * @returns boolean indicating if user features should be shown
 */
export const useShouldShowUserFeatures = (): boolean => {
  const { data: config } = useConfig();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();

  return React.useMemo(() => {
    if (!config?.APP_MODE) return false;

    // In SAAS mode, show user features if authenticated OR if there's a stored login method
    // This allows users to logout even when stuck in a 401 state
    if (config.APP_MODE === "saas") {
      return isAuthed || !!getLoginMethod();
    }

    // In OSS mode, only show user features if authenticated and Git providers are configured
    if (config.APP_MODE === "oss") {
      return isAuthed && providers.length > 0;
    }

    // For other modes, show when authenticated
    return !!isAuthed;
  }, [config?.APP_MODE, isAuthed, providers.length]);
};
