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
    }) =>
      OpenHands.updateUserConversation(variables.id, variables.conversation),
    onSuccess: (_, variables) => {
      // If the title was updated, update the Redux state
      if (variables.conversation.title !== undefined) {
        dispatch(setConversationTitle(variables.conversation.title));
      }
      
      // Invalidate the queries to refresh the data
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
    },
  });
};
