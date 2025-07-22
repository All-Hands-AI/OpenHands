import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useSearchConversations = (
  selectedRepository?: string,
  conversationTrigger?: string,
  limit: number = 20,
) =>
  useQuery({
    queryKey: [
      "conversations",
      "search",
      selectedRepository,
      conversationTrigger,
      limit,
    ],
    queryFn: () =>
      OpenHands.searchConversations(
        selectedRepository,
        conversationTrigger,
        limit,
      ),
    enabled: true, // Always enabled since parameters are optional
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
