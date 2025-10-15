import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";

export const useV1StopConversation = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { conversationId: currentConversationId } = useParams<{
    conversationId: string;
  }>();

  return useMutation({
    mutationFn: async (variables: { conversationId: string }) => {
      // First, fetch the conversation to get the sandbox_id
      const conversations =
        await V1ConversationService.batchGetAppConversations([
          variables.conversationId,
        ]);

      const conversation = conversations[0];
      if (!conversation) {
        throw new Error(`Conversation not found: ${variables.conversationId}`);
      }

      // Now pause the sandbox using the sandbox_id
      return V1ConversationService.pauseSandbox(conversation.sandbox_id);
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
    onSuccess: (_, variables) => {
      // Only redirect if we're stopping the conversation we're currently viewing
      if (
        currentConversationId &&
        variables.conversationId === currentConversationId
      ) {
        navigate("/");
      }
    },
  });
};
