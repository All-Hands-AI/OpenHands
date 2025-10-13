import { useCallback } from "react";
import { useWsClient } from "#/context/ws-client-provider";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";

/**
 * Unified hook for sending messages that works with both V0 and V1 conversations
 * - For V0 conversations: Uses Socket.IO WebSocket via useWsClient
 * - For V1 conversations: Uses HTTP POST API directly
 */
export function useSendMessage() {
  const { data: conversation } = useActiveConversation();
  const { conversationId } = useConversationId();
  const { send: v0Send } = useWsClient();

  const isV1Conversation = conversation?.conversation_version === "V1";

  const send = useCallback(
    async (event: Record<string, unknown>) => {
      if (isV1Conversation) {
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
          const content: Array<{
            type: "text" | "image_url";
            text?: string;
            image_url?: { url: string };
          }> = [
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

          // Send via V1 API
          await V1ConversationService.sendMessage(conversationId, {
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
    [isV1Conversation, conversationId, v0Send],
  );

  return { send };
}
