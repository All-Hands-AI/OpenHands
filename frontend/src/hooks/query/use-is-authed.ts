import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";
import { useAuthState } from "#/hooks/use-auth-state";

export const useIsAuthed = () => {
  const { providersAreSet } = useAuth();
  const { data: config } = useConfig();
  const isOnTosPage = useIsOnTosPage();
  const isLikelyAuthenticated = useAuthState();

  const appMode = React.useMemo(() => config?.APP_MODE, [config]);

  // Only make the API call if the user is likely authenticated
  // or if we're in OSS mode (where authentication is not required)
  const shouldCheckAuth =
    (!!appMode && appMode === "oss") || (!!appMode && isLikelyAuthenticated);

  return useQuery({
    queryKey: ["user", "authenticated", providersAreSet, appMode],
    queryFn: () => OpenHands.authenticate(appMode!),
    enabled: shouldCheckAuth && !isOnTosPage,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    retry: false,
    meta: {
      disableToast: true,
    },
  });
};
