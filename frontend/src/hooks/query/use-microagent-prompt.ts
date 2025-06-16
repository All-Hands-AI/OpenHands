import { useQuery } from "@tanstack/react-query";
import { MemoryService } from "#/api/memory-service/memory-service.api";
import { useConversationId } from "../use-conversation-id";

export const useMicroagentPrompt = (eventId: number) => {
  const { conversationId } = useConversationId();

  return useQuery({
    queryKey: ["memory", "prompt", conversationId, eventId],
    queryFn: () => MemoryService.getPrompt(conversationId!, eventId),
    enabled: !!conversationId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
