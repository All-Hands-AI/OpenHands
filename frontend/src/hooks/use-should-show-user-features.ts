import React from "react";
import { useConfig } from "./query/use-config";
import { useIsAuthed } from "./query/use-is-authed";
import { useUserProviders } from "./use-user-providers";

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
    if (!config?.APP_MODE || !isAuthed) return false;

    // In OSS mode, only show user features if Git providers are configured
    if (config.APP_MODE === "oss") {
      return providers.length > 0;
    }

    // In non-OSS modes (saas), always show user features when authenticated
    return true;
  }, [config?.APP_MODE, isAuthed, providers.length]);
};
