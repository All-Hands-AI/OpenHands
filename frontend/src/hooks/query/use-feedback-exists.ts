import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";

export interface FeedbackData {
  exists: boolean;
  rating?: number;
  reason?: string;
}

export const useFeedbackExists = (eventId?: number) => {
  const { conversationId } = useConversationId();

  return useQuery<FeedbackData>({
    queryKey: ["feedback", "exists", conversationId, eventId],
    queryFn: () => {
      if (!eventId) return { exists: false };
      return OpenHands.checkFeedbackExists(conversationId, eventId);
    },
    enabled: !!eventId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
