import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";

export const useBalance = (user: string) => {
  const { data: config } = useConfig();

  return useQuery({
    queryKey: [user, "balance"],
    queryFn: async () => ({ balance: 12.34 }),
    enabled: config?.APP_MODE === "saas",
  });
};
