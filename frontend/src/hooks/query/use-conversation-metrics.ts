import { useQuery } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { ConversationMetricsResponse } from "#/api/open-hands.types";

interface UseConversationMetricsOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

/**
 * Hook to fetch comprehensive metrics data for a conversation
 * @param conversationId The conversation ID to fetch metrics for
 * @param options Query options including enabled state and refetch interval
 * @returns Query result with metrics data
 */
export const useConversationMetrics = (
  conversationId: string | undefined,
  options: UseConversationMetricsOptions = {},
) => {
  const { enabled = true, refetchInterval } = options;

  return useQuery<ConversationMetricsResponse>({
    queryKey: ["conversation", conversationId, "metrics"],
    queryFn: () => {
      if (!conversationId) {
        throw new Error("Conversation ID is required");
      }
      return ConversationService.getConversationMetrics(conversationId);
    },
    enabled: enabled && !!conversationId,
    refetchInterval,
    staleTime: 30000, // Consider data stale after 30 seconds
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
  });
};
