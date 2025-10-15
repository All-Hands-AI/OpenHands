import { useMutation, useQueryClient } from "@tanstack/react-query";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";
import { Provider } from "#/types/settings";

export const useV1StartConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variables: {
      conversationId: string;
      providers?: Provider[];
    }) => {
      // First, fetch the conversation to get the sandbox_id
      const conversations =
        await V1ConversationService.batchGetAppConversations([
          variables.conversationId,
        ]);

      const conversation = conversations[0];
      if (!conversation) {
        throw new Error(`Conversation not found: ${variables.conversationId}`);
      }

      // Now resume the sandbox using the sandbox_id
      // Note: providers parameter is not used in V1 sandbox resume API
      return V1ConversationService.resumeSandbox(conversation.sandbox_id);
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      return { previousConversations };
    },
    onError: (_, __, context) => {
      if (context?.previousConversations) {
        queryClient.setQueryData(
          ["user", "conversations"],
          context.previousConversations,
        );
      }
    },
    onSettled: (_, __, variables) => {
      // Invalidate the specific conversation query to trigger automatic refetch
      queryClient.invalidateQueries({
        queryKey: ["user", "conversation", variables.conversationId],
      });
      // Also invalidate the conversations list for consistency
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
      // Invalidate V1 batch get queries
      queryClient.invalidateQueries({
        queryKey: ["v1-batch-get-app-conversations"],
      });
    },
  });
};
