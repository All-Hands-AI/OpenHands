import { useEffect } from "react";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useUserConversation } from "./use-user-conversation";
import OpenHands from "#/api/open-hands";

const FIVE_MINUTES = 1000 * 60 * 5;

export const useActiveConversation = () => {
  const { conversationId } = useConversationId();
  const userConversation = useUserConversation(conversationId, (query) => {
    const { data } = query.state;

    // Poll frequently if conversation is starting OR runtime is not ready
    if (
      data?.status === "STARTING" ||
      data?.runtime_status !== "STATUS$READY"
    ) {
      return 3000; // 3 seconds
    }

    return FIVE_MINUTES; // 5 minutes
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
