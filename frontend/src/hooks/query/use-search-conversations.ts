import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useSearchConversations = (
  selectedRepository?: string,
  conversationTrigger?: string,
  limit: number = 20,
  cacheDisabled: boolean = false,
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
    staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
    gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
  });
