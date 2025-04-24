import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";

// Instead of directly using useLocation, we'll check the current path manually
// This avoids the Router context requirement
const isOnTosPage = () => {
  // Only run this check in browser environment
  if (typeof window !== "undefined") {
    return window.location.pathname === "/accept-tos";
  }
  return false;
};

export const useBalance = () => {
  const { data: config } = useConfig();

  return useQuery({
    queryKey: ["user", "balance"],
    queryFn: OpenHands.getBalance,
    enabled:
      !isOnTosPage() &&
      config?.APP_MODE === "saas" &&
      config?.FEATURE_FLAGS.ENABLE_BILLING,
  });
};
