import { useMutation, useQueryClient } from "@tanstack/react-query";
import ApiKeysClient, { CreateApiKeyResponse } from "#/api/api-keys";
import { API_KEYS_QUERY_KEY } from "#/hooks/query/use-api-keys";

export function useCreateApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (name: string): Promise<CreateApiKeyResponse> =>
      ApiKeysClient.createApiKey(name),
    onSuccess: () => {
      // Invalidate the API keys query to trigger a refetch
      queryClient.invalidateQueries({ queryKey: [API_KEYS_QUERY_KEY] });
    },
  });
}
