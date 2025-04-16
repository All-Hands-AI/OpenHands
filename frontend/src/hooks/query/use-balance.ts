import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";
import { useDisableApiOnTos } from "../use-disable-api-on-tos";

export const useBalance = () => {
  const { data: config } = useConfig();
  const disableApiCalls = useDisableApiOnTos();

  return useQuery({
    queryKey: ["user", "balance"],
    queryFn: OpenHands.getBalance,
    enabled:
      !disableApiCalls &&
      config?.APP_MODE === "saas" &&
      config?.FEATURE_FLAGS?.ENABLE_BILLING,
  });
};
