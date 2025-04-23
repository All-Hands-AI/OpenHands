import { useMutation, useQueryClient } from "@tanstack/react-query";
import ApiKeysClient from "#/api/api-keys";
import { API_KEYS_QUERY_KEY } from "#/hooks/query/use-api-keys";

export function useDeleteApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await ApiKeysClient.deleteApiKey(id);
    },
    onSuccess: () => {
      // Invalidate the API keys query to trigger a refetch
      queryClient.invalidateQueries({ queryKey: [API_KEYS_QUERY_KEY] });
    },
  });
}
