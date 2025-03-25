import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "../query/use-config";

export const useLogout = () => {
  const { setProviderTokensSet, setProvidersAreSet } = useAuth();
  const queryClient = useQueryClient();
  const { data: config } = useConfig();

  return useMutation({
    mutationFn: async () => {
      // Pause all queries that depend on githubTokenIsSet
      queryClient.setQueryData(["user"], null);

      // Call logout endpoint
      await OpenHands.logout(config?.APP_MODE ?? "oss");

      // Remove settings from cache so it will be refetched with new token state
      queryClient.removeQueries({ queryKey: ["settings"] });

      // Update token state - this will trigger a settings refetch since it's part of the query key
      setProviderTokensSet([]);
      setProvidersAreSet(false);
    },
  });
};
