import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";

export const useIsAuthed = () => {
  const { gitHubToken } = useAuth();
  const { data: config } = useConfig();

  const appMode = React.useMemo(() => config?.APP_MODE, [config]);

  return useQuery({
    queryKey: ["user", "authenticated", gitHubToken, appMode],
    queryFn: () => OpenHands.authenticate(gitHubToken || "", appMode!),
    enabled: !!appMode,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
