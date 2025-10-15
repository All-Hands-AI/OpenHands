import { useQuery } from "@tanstack/react-query";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";

export const V1_BATCH_GET_APP_CONVERSATIONS_QUERY_KEY =
  "v1-batch-get-app-conversations";

/**
 * Hook to batch fetch V1 app conversations by their IDs
 * Returns null for any missing conversations
 *
 * @param ids Array of conversation IDs to fetch (max 100)
 * @param enabled Whether the query should run (default: true if ids.length > 0)
 */
export function useV1BatchGetAppConversations(
  ids: string[],
  enabled?: boolean,
) {
  return useQuery({
    queryKey: [V1_BATCH_GET_APP_CONVERSATIONS_QUERY_KEY, ids],
    queryFn: () => V1ConversationService.batchGetAppConversations(ids),
    enabled: enabled ?? ids.length > 0,
    staleTime: 1000 * 30, // 30 seconds
    gcTime: 1000 * 60 * 5, // 5 minutes
  });
}
