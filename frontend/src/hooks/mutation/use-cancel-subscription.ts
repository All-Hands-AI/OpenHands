import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useCancelSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: OpenHands.cancelSubscription,
    onSuccess: () => {
      // Invalidate subscription access query to refresh the UI
      queryClient.invalidateQueries({
        queryKey: ["user", "subscription_access"],
      });
    },
  });
};
