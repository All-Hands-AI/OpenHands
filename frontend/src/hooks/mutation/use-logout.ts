import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "../query/use-config";

export const useLogout = () => {
  const { setGitHubTokenIsSet } = useAuth();
  const queryClient = useQueryClient();
  const { data: config } = useConfig();

  return useMutation({
    mutationFn: async () => {
      // Pause all queries that depend on githubTokenIsSet
      queryClient.setQueryData(["user"], null);
      
      // Call logout endpoint
      await OpenHands.logout(config?.APP_MODE ?? "oss");
      
      // Update token state
      setGitHubTokenIsSet(false);
      
      // Refetch settings to get updated token state
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
};
