import { useQuery } from "@tanstack/react-query";
import ApiKeysClient, { ApiKey } from "#/api/api-keys";
import { useConfig } from "./use-config";

export const API_KEYS_QUERY_KEY = "api-keys";

export function useApiKeys() {
  const { data: config } = useConfig();

  return useQuery<ApiKey[]>({
    queryKey: [API_KEYS_QUERY_KEY],
    queryFn: async () => {
      const keys = await ApiKeysClient.getApiKeys();
      return Array.isArray(keys) ? keys : [];
    },
    enabled: config?.APP_MODE === "saas",
  });
}
