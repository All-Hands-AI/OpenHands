import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useSettings } from "./use-settings";

export const useIsAuthed = () => {
  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  const appMode = React.useMemo(() => config?.APP_MODE, [config]);

  return useQuery({
    queryKey: ["user", "authenticated", settings?.GITHUB_TOKEN_IS_SET, appMode],
    queryFn: () => OpenHands.authenticate(appMode!),
    enabled: !!appMode,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  });
};
