import { useQuery } from "@tanstack/react-query";
import { useConversation } from "#/context/conversation-context";
import OpenHands from "#/api/open-hands";

export const useSearchEvents = (params: {
  query?: string;
  startId?: number;
  limit?: number;
  eventType?: string;
  source?: string;
  startDate?: string;
  endDate?: string;
}) => {
  const { conversationId } = useConversation();

  return useQuery({
    queryKey: ["search_events", conversationId, params],
    queryFn: () => {
      if (!conversationId) throw new Error("No conversation ID");
      return OpenHands.searchEvents(conversationId, params);
    },
    enabled: !!conversationId,
  });
};
