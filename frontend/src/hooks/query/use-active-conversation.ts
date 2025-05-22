import { useConversation } from "#/context/conversation-context";
import { useUserConversation } from "./use-user-conversation";

const FIVE_MINUTES = 1000 * 60 * 5;

export const useActiveConversation = () => {
  const { conversationId } = useConversation();
  return useUserConversation(conversationId, (query) => {
    if (query.state.data?.status === "STARTING") {
      return 2000; // 2 seconds
    }
    return FIVE_MINUTES;
  });
};
