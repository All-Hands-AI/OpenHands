import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useCreateSubscriptionCheckoutSession = () =>
  useMutation({
    mutationFn: OpenHands.createSubscriptionCheckoutSession,
    onSuccess: (data) => {
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      }
    },
  });
