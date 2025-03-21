import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

/**
 * Hook to fetch a single conversation by ID
 *
 * @param cid Conversation ID
 * @returns Query result with the conversation data
 */
export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => OpenHands.getConversation(cid!),
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
