import { useCallback } from "react";
import { useWsClient } from "#/context/ws-client-provider";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useConversationWebSocket } from "#/contexts/conversation-websocket-context";
import { V1MessageContent } from "#/api/conversation-service/v1-conversation-service.types";

/**
 * Unified hook for sending messages that works with both V0 and V1 conversations
 * - For V0 conversations: Uses Socket.IO WebSocket via useWsClient
 * - For V1 conversations: Uses native WebSocket via ConversationWebSocketProvider
 */
export function useSendMessage() {
  const { data: conversation } = useActiveConversation();
  const { send: v0Send } = useWsClient();

  // Get V1 context (will be null if not in V1 provider)
  const v1Context = useConversationWebSocket();

  const isV1Conversation = conversation?.conversation_version === "V1";

  const send = useCallback(
    async (event: Record<string, unknown>) => {
      if (isV1Conversation && v1Context) {
        // V1: Convert V0 event format to V1 message format
        const { action, args } = event as {
          action: string;
          args?: {
            content?: string;
            image_urls?: string[];
            file_urls?: string[];
            timestamp?: string;
          };
        };

        if (action === "message" && args?.content) {
          // Build V1 message content array
          const content: Array<V1MessageContent> = [
            {
              type: "text",
              text: args.content,
            },
          ];

          // Add images if present
          if (args.image_urls && args.image_urls.length > 0) {
            args.image_urls.forEach((url) => {
              content.push({
                type: "image_url",
                image_url: { url },
              });
            });
          }

          // Send via V1 WebSocket context (uses correct host/port)
          await v1Context.sendMessage({
            role: "user",
            content,
          });
        } else {
          // For non-message events, fall back to V0 send
          // (e.g., agent state changes, other control events)
          v0Send(event);
        }
      } else {
        // V0: Use Socket.IO
        v0Send(event);
      }
    },
    [isV1Conversation, v1Context, v0Send],
  );

  return { send };
}
