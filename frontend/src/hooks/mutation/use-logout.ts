import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";

export const useLogout = () => {
  const { setGitHubTokenIsSet } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: OpenHands.logout,
    onSuccess: async () => {
      setGitHubTokenIsSet(false);
      await queryClient.invalidateQueries();
    },
  });
};
