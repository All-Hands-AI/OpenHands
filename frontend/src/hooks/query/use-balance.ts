import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";
import { useAuthState } from "#/hooks/use-auth-state";

export const useBalance = () => {
  const { data: config } = useConfig();
  const isOnTosPage = useIsOnTosPage();
  const isLikelyAuthenticated = useAuthState();

  return useQuery({
    queryKey: ["user", "balance"],
    queryFn: OpenHands.getBalance,
    enabled:
      !isOnTosPage &&
      config?.APP_MODE === "saas" &&
      config?.FEATURE_FLAGS.ENABLE_BILLING &&
      isLikelyAuthenticated, // Only fetch balance if user is likely authenticated
  });
};
