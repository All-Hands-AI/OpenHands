import { useMutation } from "@tanstack/react-query";
import BillingService from "#/api/billing-service/billing-service.api";

export const useCreateSubscriptionCheckoutSession = () =>
  useMutation({
    mutationFn: BillingService.createSubscriptionCheckoutSession,
    onSuccess: (data) => {
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      }
    },
  });
