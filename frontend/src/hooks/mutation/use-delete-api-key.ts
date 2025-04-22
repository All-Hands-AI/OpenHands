import { useMutation, useQueryClient } from "@tanstack/react-query";
import ApiKeysClient from "#/api/api-keys";
import { API_KEYS_QUERY_KEY } from "#/hooks/query/use-api-keys";
import { useConfig } from "#/hooks/query/use-config";

export function useDeleteApiKey() {
  const queryClient = useQueryClient();
  const { data: config } = useConfig();
  const isSaasMode = config?.APP_MODE === "saas";

  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await ApiKeysClient.deleteApiKey(id);
    },
    onSuccess: () => {
      // Invalidate the API keys query to trigger a refetch
      queryClient.invalidateQueries({ queryKey: [API_KEYS_QUERY_KEY] });
    },
    meta: {
      // This is used for documentation purposes to indicate when this mutation is available
      enabled: isSaasMode,
    },
  });
}
