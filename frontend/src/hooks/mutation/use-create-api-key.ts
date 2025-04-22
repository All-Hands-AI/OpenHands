import { useMutation, useQueryClient } from "@tanstack/react-query";
import ApiKeysClient, { CreateApiKeyResponse } from "#/api/api-keys";
import { API_KEYS_QUERY_KEY } from "#/hooks/query/use-api-keys";
import { useConfig } from "#/hooks/query/use-config";

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  const { data: config } = useConfig();
  const isSaasMode = config?.APP_MODE === "saas";

  return useMutation({
    mutationFn: async (name: string): Promise<CreateApiKeyResponse> =>
      ApiKeysClient.createApiKey(name),
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
