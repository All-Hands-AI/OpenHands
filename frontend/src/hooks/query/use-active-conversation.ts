import { useEffect } from "react";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useUserConversation } from "./use-user-conversation";
import ConversationService from "#/api/conversation-service/conversation-service.api";

export const useActiveConversation = () => {
  const { conversationId } = useConversationId();
  const userConversation = useUserConversation(conversationId, (query) => {
    const status = query.state.data?.status;
    console.log('[CONVERSATION_DEBUG] Polling conversation:', {
      conversationId,
      status,
      runtime_status: query.state.data?.runtime_status,
      timestamp: new Date().toISOString()
    });

    if (status === "STARTING") {
      console.log('[CONVERSATION_DEBUG] Status is STARTING, polling every 3s');
      return 3000; // 3 seconds
    }
    // TODO: Return conversation title as a WS event to avoid polling
    // This was changed from 5 minutes to 30 seconds to poll for updated conversation title after an auto update
    console.log('[CONVERSATION_DEBUG] Status is not STARTING, polling every 30s');
    return 30000; // 30 seconds
  });

  useEffect(() => {
    const conversation = userConversation.data;
    ConversationService.setCurrentConversation(conversation || null);
  }, [
    conversationId,
    userConversation.isFetched,
    userConversation?.data?.status,
  ]);
  return userConversation;
};
