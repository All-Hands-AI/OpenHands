import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";

export const useIsAuthed = () => {
  const { providersAreSet } = useAuth();
  const { data: config } = useConfig();

  const appMode = React.useMemo(() => config?.APP_MODE, [config]);

  return useQuery({
    queryKey: ["user", "authenticated", providersAreSet, appMode],
    queryFn: () => OpenHands.authenticate(appMode!),
    enabled: !!appMode,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    retry: false,
    meta: {
      disableToast: true,
    },
  });
};
