import { useQuery, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useConfig } from "#/hooks/query/use-config";

export interface FeedbackData {
  exists: boolean;
  rating?: number;
  reason?: string;
}

export const useFeedbackExists = (eventId?: number) => {
  const { conversationId } = useConversationId();
  const { data: config } = useConfig();
  const queryClient = useQueryClient();

  // Check if we already have this data in the cache
  const queryKey = ["feedback", "exists", conversationId, eventId];
  const cachedData = queryClient.getQueryData<FeedbackData>(queryKey);

  return useQuery<FeedbackData>({
    queryKey,
    queryFn: () => {
      if (!eventId) return { exists: false };

      // If we already have cached data showing feedback exists, return it immediately
      if (cachedData?.exists) {
        return cachedData;
      }

      return OpenHands.checkFeedbackExists(conversationId, eventId);
    },
    enabled: !!eventId && config?.APP_MODE === "saas",
    staleTime: 1000 * 60 * 60, // Increase to 60 minutes since feedback rarely changes
    gcTime: 1000 * 60 * 60 * 2, // 2 hours
    // Prevent refetching on window focus to reduce duplicate requests
    refetchOnWindowFocus: false,
    // Prevent refetching on reconnect to reduce duplicate requests
    refetchOnReconnect: false,
  });
};
