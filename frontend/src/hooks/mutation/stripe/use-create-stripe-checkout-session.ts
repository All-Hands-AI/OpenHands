import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useCreateStripeCheckoutSession = () =>
  useMutation({
    mutationFn: (variables: { amount: number }) =>
      OpenHands.createCheckoutSession(variables.amount),
  });
