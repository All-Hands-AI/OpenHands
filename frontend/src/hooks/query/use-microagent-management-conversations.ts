import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

export const useMicroagentManagementConversations = (
  pageId?: string,
  limit: number = 100,
  selectedRepository?: string,
  cacheDisabled: boolean = false,
) =>
  useQuery({
    queryKey: [
      "conversations",
      "microagent-management",
      pageId,
      limit,
      selectedRepository,
    ],
    queryFn: () =>
      OpenHands.getMicroagentManagementConversations(
        pageId,
        selectedRepository,
        limit,
      ),
    staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
    gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
  });
