import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import ConversationService from "#/api/conversation-service/conversation-service.api";

export const useStopConversation = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { conversationId: currentConversationId } = useParams<{
    conversationId: string;
  }>();

  return useMutation({
    mutationFn: (variables: { conversationId: string }) =>
      ConversationService.stopConversation(variables.conversationId),
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
