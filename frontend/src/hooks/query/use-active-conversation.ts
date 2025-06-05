import { useEffect } from "react";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useUserConversation } from "./use-user-conversation";
import OpenHands from "#/api/open-hands";

const FIVE_MINUTES = 1000 * 60 * 5;

export const useActiveConversation = () => {
  const { conversationId } = useConversationId();
  const userConversation = useUserConversation(conversationId, (query) => {
    if (["STOPPED", "STARTING"].includes(query.state.data?.status || "")) {
      return 3000; // 3 seconds
    }
    return FIVE_MINUTES;
  });

  useEffect(() => {
    const conversation = userConversation.data;
    console.log("TRACE:setCurrentConversation", conversation);
    OpenHands.setCurrentConversation(conversation || null);
  }, [conversationId, userConversation.isFetched]);
  return userConversation;
};
