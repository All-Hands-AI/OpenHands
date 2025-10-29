import { useMutation, useQueryClient } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { normalizeConversationId } from "#/utils/utils";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: {
      conversationId: string;
      newTitle: string;
      conversationVersion?: "V0" | "V1";
    }) =>
      ConversationService.updateConversation(variables.conversationId, {
        title: variables.newTitle,
      }),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      // Normalize the conversation ID based on conversation version
      const normalizedConversationId = normalizeConversationId(
        variables.conversationId,
        variables.conversationVersion,
      );

      queryClient.setQueryData(
        ["user", "conversations"],
        (old: { conversation_id: string; title: string }[] | undefined) =>
          old?.map((conv) =>
            conv.conversation_id === variables.conversationId
              ? { ...conv, title: variables.newTitle }
              : conv,
          ),
      );

      // Also optimistically update the active conversation query using normalized ID
      queryClient.setQueryData(
        ["user", "conversation", normalizedConversationId],
        (old: { title: string } | undefined) =>
          old ? { ...old, title: variables.newTitle } : old,
      );

      return { previousConversations };
    },
    onError: (err, variables, context) => {
      if (context?.previousConversations) {
        queryClient.setQueryData(
          ["user", "conversations"],
          context.previousConversations,
        );
      }
    },
    onSettled: (data, error, variables) => {
      // Normalize the conversation ID based on conversation version
      const normalizedConversationId = normalizeConversationId(
        variables.conversationId,
        variables.conversationVersion,
      );

      // Invalidate and refetch the conversation list to show the updated title
      queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });

      // Also invalidate the specific conversation query using normalized ID
      queryClient.invalidateQueries({
        queryKey: ["user", "conversation", normalizedConversationId],
      });
    },
  });
};
