import React from "react";
import { generateAuthUrl } from "#/utils/generate-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";
import { useAuth } from "#/context/auth-context";
import { useDisableApiOnTos } from "./use-disable-api-on-tos";

interface UseAuthUrlConfig {
  appMode: GetConfigResponse["APP_MODE"] | null;
  identityProvider: string;
}

export const useAuthUrl = (config: UseAuthUrlConfig) => {
  const { providersAreSet } = useAuth();
  const disableApiCalls = useDisableApiOnTos();

  return React.useMemo(() => {
    // Disable auth URL generation on TOS page
    if (disableApiCalls) {
      return null;
    }

    if (config.appMode === "saas" && !providersAreSet) {
      try {
        return generateAuthUrl(
          config.identityProvider,
          new URL(window.location.href),
        );
      } catch (e) {
        // In test environment, window.location.href might not be a valid URL
        return null;
      }
    }

    return null;
  }, [
    providersAreSet,
    config.appMode,
    config.identityProvider,
    disableApiCalls,
  ]);
};
