import { useQuery } from "@tanstack/react-query";
import ApiKeysClient from "#/api/api-keys";

export const API_KEYS_QUERY_KEY = "api-keys";

export function useApiKeys() {
  return useQuery({
    queryKey: [API_KEYS_QUERY_KEY],
    queryFn: async () => {
      const keys = await ApiKeysClient.getApiKeys();
      return Array.isArray(keys) ? keys : [];
    },
  });
}
