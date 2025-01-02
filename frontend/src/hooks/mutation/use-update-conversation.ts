import { useQueryClient, useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Conversation } from "#/api/open-hands.types";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { id: string; title: Conversation["title"] }) =>
      OpenHands.updateUserConversationTitle(variables.id, variables.title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
    },
  });
};
