import { useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";

export const useIsAuthed = () => {
  const queryClient = useQueryClient();
  const { githubTokenIsSet, setGitHubTokenIsSet } = useAuth();
  const { data: config } = useConfig();

  const appMode = config?.APP_MODE;

  const query = useQuery({
    queryKey: ["user", "authenticated", githubTokenIsSet, appMode],
    queryFn: () => OpenHands.authenticate(appMode!),
    enabled: !!appMode,
    retry: false,
    meta: {
      disableToast: true,
    },
  });

  React.useEffect(() => {
    if (query.isError) {
      queryClient.invalidateQueries();
      setGitHubTokenIsSet(false);
    }
  }, [query.isError]);

  return query;
};
