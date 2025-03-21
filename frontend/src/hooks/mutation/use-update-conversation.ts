import { useQueryClient, useMutation } from "@tanstack/react-query";
import { useDispatch } from "react-redux";
import OpenHands from "#/api/open-hands";
import { Conversation } from "#/api/open-hands.types";
import { setConversationTitle } from "#/state/conversation-slice";

export const useUpdateConversation = () => {
  const queryClient = useQueryClient();
  const dispatch = useDispatch();

  return useMutation({
    mutationFn: (variables: {
      id: string;
      conversation: Partial<Omit<Conversation, "id">>;
    }) => {
      // If the title is being updated, update the Redux state immediately
      // This ensures the document title is updated right away
      if (variables.conversation.title !== undefined) {
        dispatch(setConversationTitle(variables.conversation.title));
      }

      return OpenHands.updateUserConversation(
        variables.id,
        variables.conversation,
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
    },
  });
};
