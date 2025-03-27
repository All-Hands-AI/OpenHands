import { useQuery } from "@tanstack/react-query";
import { conversationService } from "#/api/conversation-service/conversation-service.api";

export const useUserConversation = (cid: string | null) =>
  useQuery({
    queryKey: ["user", "conversation", cid],
    queryFn: () => conversationService.getConversation(cid!),
    enabled: !!cid,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
