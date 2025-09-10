import { useEffect } from "react";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useUserConversation } from "./use-user-conversation";
import OpenHands from "#/api/open-hands";

export const useActiveConversation = () => {
  const { conversationId } = useConversationId();
  const userConversation = useUserConversation(conversationId, (query) => {
    if (query.state.data?.status === "STARTING") {
      return 3000; // 3 seconds
    }
    // TODO: Return conversation title as a WS event to avoid polling
    // This was changed from 5 minutes to 30 seconds to poll for updated conversation title after an auto update
    return 30000; // 30 seconds
  });

  useEffect(() => {
    const conversation = userConversation.data;
    OpenHands.setCurrentConversation(conversation || null);
  }, [
    conversationId,
    userConversation.isFetched,
    userConversation?.data?.status,
  ]);
  return userConversation;
};
