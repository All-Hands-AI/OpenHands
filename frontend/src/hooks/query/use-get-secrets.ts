import { useQuery } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";
import { useConfig } from "./use-config";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useUserProviders } from "#/hooks/use-user-providers";
import React from "react";

export const useGetSecrets = () => {
  const { data: config } = useConfig();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();

  // Only enable the query if:
  // - We have a valid APP_MODE, AND
  // - Either we're not in OSS mode and user is authenticated OR we're in OSS mode and have provider tokens configured
  const shouldFetchSecrets = React.useMemo(() => {
    if (!config?.APP_MODE) return false;

    // In OSS mode, only fetch secrets if Git providers are configured
    if (config.APP_MODE === "oss") {
      return providers.length > 0;
    }

    // In non-OSS modes (saas), only fetch secrets when authenticated
    return isAuthed;
  }, [config?.APP_MODE, isAuthed, providers.length]);

  return useQuery({
    queryKey: ["secrets"],
    queryFn: SecretsService.getSecrets,
    enabled: shouldFetchSecrets,
  });
};
