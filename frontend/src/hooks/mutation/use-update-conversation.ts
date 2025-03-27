import { useQueryClient, useMutation } from "@tanstack/react-query";
import { ConversationService } from "#/api/conversation-service/conversation-service.api";
import { UpdateConversationBody } from "#/api/conversation-service/conversation-service.types";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: {
      id: string;
      conversation: UpdateConversationBody;
    }) =>
      ConversationService.updateConversation(
        variables.id,
        variables.conversation,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
};
