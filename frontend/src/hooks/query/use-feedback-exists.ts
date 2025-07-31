import { useQuery } from "@tanstack/react-query";
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

  return useQuery<FeedbackData>({
    queryKey: ["feedback", "exists", conversationId, eventId],
    queryFn: () => {
      if (!eventId) return { exists: false };
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
