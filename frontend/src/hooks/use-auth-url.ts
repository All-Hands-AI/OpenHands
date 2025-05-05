import { generateAuthUrl } from "#/utils/generate-auth-url";
import { GetConfigResponse } from "#/api/open-hands.types";

interface UseAuthUrlConfig {
  appMode: GetConfigResponse["APP_MODE"] | null;
  identityProvider: string;
}

export const useAuthUrl = (config: UseAuthUrlConfig) =>
  generateAuthUrl(config.identityProvider, new URL(window.location.href));
