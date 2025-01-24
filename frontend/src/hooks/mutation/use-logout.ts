import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: OpenHands.logout,
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
};
