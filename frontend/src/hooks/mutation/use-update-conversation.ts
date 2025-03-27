import { useQueryClient, useMutation } from "@tanstack/react-query";
import { Conversation } from "#/api/open-hands.types";
import { conversationService } from "#/api/conversation-service/conversation-service.api";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: {
      id: string;
      conversation: Partial<Omit<Conversation, "id">>;
    }) =>
      conversationService.updateConversation(
        variables.id,
        variables.conversation,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
    },
  });
};
