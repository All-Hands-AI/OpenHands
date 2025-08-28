import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";

export const useSubscriptionAccess = () => {
  const { data: config } = useConfig();
  const isOnTosPage = useIsOnTosPage();

  return useQuery({
    queryKey: ["user", "subscription_access"],
    queryFn: OpenHands.getSubscriptionAccess,
    enabled:
      !isOnTosPage &&
      config?.APP_MODE === "saas" &&
      config?.FEATURE_FLAGS?.ENABLE_BILLING,
  });
};
