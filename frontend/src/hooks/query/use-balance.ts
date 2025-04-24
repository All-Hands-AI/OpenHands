import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";

export const useBalance = () => {
  const { data: config } = useConfig();
  const { pathname } = useLocation();
  const isOnTosPage = pathname === "/accept-tos";

  return useQuery({
    queryKey: ["user", "balance"],
    queryFn: OpenHands.getBalance,
    enabled:
      !isOnTosPage &&
      config?.APP_MODE === "saas" &&
      config?.FEATURE_FLAGS.ENABLE_BILLING,
  });
};
