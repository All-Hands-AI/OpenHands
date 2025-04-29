import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";

export const useIsAuthed = () => {
  const { providersAreSet } = useAuth();
  const { data: config } = useConfig();
  const isOnTosPage = useIsOnTosPage();

  const appMode = React.useMemo(() => config?.APP_MODE, [config]);

  return useQuery({
    queryKey: ["user", "authenticated", providersAreSet, appMode],
    queryFn: () => OpenHands.authenticate(appMode!),
    enabled: !!appMode && !isOnTosPage,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    retry: false,
    meta: {
      disableToast: true,
    },
  });
};
