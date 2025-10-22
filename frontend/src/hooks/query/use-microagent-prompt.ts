import { useQuery } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useConversationId } from "../use-conversation-id";
import { useActiveConversation } from "./use-active-conversation";

export const useMicroagentPrompt = (eventId: number) => {
  const { conversationId } = useConversationId();
  const { data: conversation } = useActiveConversation();

  // TODO: Disable remember-prompt API call for V1 conversations
  // This is a temporary measure and may be re-enabled in the future
  const isV1Conversation = conversation?.conversation_version === "V1";

  return useQuery({
    queryKey: ["memory", "prompt", conversationId, eventId],
    queryFn: () =>
      ConversationService.getMicroagentPrompt(conversationId!, eventId),
    enabled: !!conversationId && !isV1Conversation, // Disable for V1 conversations
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
