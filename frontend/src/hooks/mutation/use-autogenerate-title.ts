import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { autogenerateConversationTitle } from "#/services/conversation-title-service";

export const useAutogenerateTitle = () => {
  const { conversationId } = useConversation();

  return useMutation({
    mutationFn: () =>
      autogenerateConversationTitle(conversationId),
  });
};
