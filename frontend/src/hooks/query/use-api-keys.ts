import { useQuery } from "@tanstack/react-query";
import ApiKeysClient from "#/api/api-keys";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";

export const API_KEYS_QUERY_KEY = "api-keys";

export function useApiKeys() {
  const { providersAreSet } = useAuth();
  const { data: config } = useConfig();

  return useQuery({
    queryKey: [API_KEYS_QUERY_KEY],
    enabled: providersAreSet && config?.APP_MODE === "saas",
    queryFn: async () => {
      const keys = await ApiKeysClient.getApiKeys();
      return Array.isArray(keys) ? keys : [];
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
