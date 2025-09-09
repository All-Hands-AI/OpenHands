import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useCreateSubscriptionCheckoutSession = () =>
  useMutation({
    mutationFn: async () => {
      const response = await OpenHands.createSubscriptionCheckoutSession();
      if (response.redirect_url) {
        window.open(response.redirect_url, "_blank");
      }
    },
  });
