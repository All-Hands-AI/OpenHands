import { useQuery } from "@tanstack/react-query";
import { ConversationService } from "#/api/conversation-service/conversation-service.api";

export const useConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["conversations", cid],
    queryFn: () => ConversationService.getConversation(cid!),
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
