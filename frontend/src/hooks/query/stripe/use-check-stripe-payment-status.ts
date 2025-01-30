import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useCheckStripePaymentStatus = (sessionId: string | undefined) =>
  useQuery({
    queryKey: ["checkout-session", sessionId],
    queryFn: async () => OpenHands.checkSessionStatus(sessionId!),
    enabled: !!sessionId,
  });
