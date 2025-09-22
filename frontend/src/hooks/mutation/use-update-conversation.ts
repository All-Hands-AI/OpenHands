import { useMutation, useQueryClient } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { conversationId: string; newTitle: string }) =>
      ConversationService.updateConversation(variables.conversationId, {
        title: variables.newTitle,
      }),
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      queryClient.setQueryData(
        ["user", "conversations"],
        (old: { conversation_id: string; title: string }[] | undefined) =>
          old?.map((conv) =>
            conv.conversation_id === variables.conversationId
              ? { ...conv, title: variables.newTitle }
              : conv,
          ),
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
    onSuccess: async (data, variables) => {
      // Cancel any ongoing queries for this conversation to prevent race conditions
      await queryClient.cancelQueries({
        queryKey: ["user", "conversation", variables.conversationId],
      });

      // Update the individual conversation cache immediately with the new title
      queryClient.setQueryData(
        ["user", "conversation", variables.conversationId],
        (oldData: unknown) => {
          if (oldData && typeof oldData === "object") {
            return { ...oldData, title: variables.newTitle };
          }
          return oldData;
        },
      );

      // Invalidate and refetch the conversation list to show the updated title
      queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });

      // Delay invalidation of the individual conversation to allow backend persistence
      // and prevent immediate race conditions with polling
      setTimeout(() => {
        queryClient.invalidateQueries({
          queryKey: ["user", "conversation", variables.conversationId],
        });
      }, 5000); // 5 second delay to allow backend to persist
    },
  });
};
