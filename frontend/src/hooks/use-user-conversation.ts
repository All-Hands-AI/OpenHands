import { useGetUserConversationQuery } from "../api/slices";
import { useConversation } from "../context/conversation-context";

export const useUserConversation = () => {
  const { conversationId } = useConversation();
  return useGetUserConversationQuery(conversationId);
};
