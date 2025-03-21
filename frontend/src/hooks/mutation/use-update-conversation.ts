import { useQueryClient, useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Conversation } from "#/api/open-hands.types";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: {
      id: string;
      conversation: Partial<Omit<Conversation, "id">>;
    }) => {
      console.log("[useUpdateConversation] Mutation called with:", variables);
      return OpenHands.updateUserConversation(
        variables.id,
        variables.conversation,
      );
    },
    onSuccess: () => {
      console.log("[useUpdateConversation] Mutation succeeded");
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
    },
    onError: (error) => {
      console.error("[useUpdateConversation] Mutation failed:", error);
    },
  });
};
