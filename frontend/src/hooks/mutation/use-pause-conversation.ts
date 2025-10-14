import { useMutation, useQueryClient } from "@tanstack/react-query";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

export const usePauseConversation = () => {
  const queryClient = useQueryClient();
  const { conversationId } = useConversationId();
  const { data: conversation } = useActiveConversation();

  return useMutation({
    mutationFn: async () => {
      if (!conversation) {
        throw new Error("No active conversation found");
      }

      return V1ConversationService.pauseConversation(
        conversationId,
        conversation.url,
        conversation.session_api_key,
      );
    },
    onSuccess: () => {
      // Invalidate the specific conversation query to trigger automatic refetch
      queryClient.invalidateQueries({
        queryKey: ["user", "conversation", conversationId],
      });
    },
  });
};
