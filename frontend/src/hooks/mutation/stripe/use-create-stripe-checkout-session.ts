import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useCreateStripeCheckoutSession = () =>
  useMutation({
    mutationFn: async (variables: { amount: number }) => {
      const redirectUrl = await OpenHands.createCheckoutSession(
        variables.amount,
      );
      window.location.href = redirectUrl;
    },
  });
