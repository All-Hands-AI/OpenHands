import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import OpenHands from "#/api/open-hands";

export const useBalance = (user: string) => {
  const { data: config } = useConfig();

  return useQuery({
    queryKey: [user, "balance"],
    queryFn: OpenHands.getBalance,
    // TODO: Should be saas-only and if user is
    enabled: config?.APP_MODE !== "saas",
  });
};
