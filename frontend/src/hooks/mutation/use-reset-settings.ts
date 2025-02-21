import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useResetSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: OpenHands.resetSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
};
