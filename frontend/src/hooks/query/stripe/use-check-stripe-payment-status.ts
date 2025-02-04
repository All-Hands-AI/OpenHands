import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

// TODO: This should probably be removed from the API now that we are using the stripe hosted UI
export const useCheckStripePaymentStatus = (sessionId: string | undefined) =>
  useQuery({
    queryKey: ["checkout-session", sessionId],
    queryFn: async () => OpenHands.checkSessionStatus(sessionId!),
    enabled: !!sessionId,
  });
