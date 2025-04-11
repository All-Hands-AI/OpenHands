import React from "react";
import { generateAuthUrl } from "#/utils/generate-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";
import { useAuth } from "#/context/auth-context";

interface UseAuthUrlConfig {
  appMode: GetConfigResponse["APP_MODE"] | null;
  identityProvider: string;
}

export const useAuthUrl = (config: UseAuthUrlConfig) => {
  const { providersAreSet } = useAuth();

  return React.useMemo(() => {
    if (config.appMode === "saas" && !providersAreSet)
      return generateAuthUrl(
        config.identityProvider,
        new URL(window.location.href),
      );

    return null;
  }, [providersAreSet, config.appMode, config.identityProvider]);
};
