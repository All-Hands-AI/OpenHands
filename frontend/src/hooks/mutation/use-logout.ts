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
      setGitHubTokenIsSet(false);
      await queryClient.invalidateQueries();
      await OpenHands.logout(config?.APP_MODE ?? "oss");
    },
  });
};
