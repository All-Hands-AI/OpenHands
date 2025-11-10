import { useMutation } from "@tanstack/react-query";
import BillingService from "#/api/billing-service/billing-service.api";

export const useCreateStripeCheckoutSession = () =>
  useMutation({
    mutationFn: async (variables: { amount: number }) => {
      const redirectUrl = await BillingService.createCheckoutSession(
        variables.amount,
      );
      window.location.href = redirectUrl;
    },
  });
