import { useMemo } from "react";
import { useWsClient, WebSocketStatus } from "#/context/ws-client-provider";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";

/**
 * Unified hook that returns the current WebSocket status
 * - For V0 conversations: Returns status from useWsClient
 * - For V1 conversations: Returns CONNECTED (WebSocket status is managed internally)
 */
export function useWebSocketStatus(): WebSocketStatus {
  const { data: conversation } = useActiveConversation();
  const v0Status = useWsClient();

  const isV1Conversation = conversation?.conversation_version === "V1";

  const webSocketStatus = useMemo(() => {
    if (isV1Conversation) {
      // For V1 conversations, return CONNECTED
      // The actual connection state is managed internally by ConversationWebSocketProvider
      return "CONNECTED";
    }
    return v0Status.webSocketStatus;
  }, [isV1Conversation, v0Status.webSocketStatus]);

  return webSocketStatus;
}
