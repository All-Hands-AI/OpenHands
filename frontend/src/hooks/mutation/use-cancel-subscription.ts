import { useMutation, useQueryClient } from "@tanstack/react-query";
import BillingService from "#/api/billing-service/billing-service.api";

export const useCancelSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: BillingService.cancelSubscription,
    onSuccess: () => {
      // Invalidate subscription access query to refresh the UI
      queryClient.invalidateQueries({
        queryKey: ["user", "subscription_access"],
      });
    },
  });
};
