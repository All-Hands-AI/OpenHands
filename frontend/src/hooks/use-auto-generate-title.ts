import { useEffect, useRef } from "react";
import { useParams } from "react-router";
import { useUpdateConversation } from "./mutation/use-update-conversation";

/**
 * Hook to auto-generate a conversation title after the first user message is sent.
 * It triggers a title update request with an empty title, which will cause the backend
 * to auto-generate a title based on the first user message.
 *
 * @param messageCount The current number of messages in the conversation
 */
export function useAutoGenerateTitle(messageCount: number) {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { mutate: updateConversation } = useUpdateConversation();
  const hasTitleBeenGenerated = useRef(false);

  useEffect(() => {
    // Only trigger title generation after the first user message (when messageCount becomes 1)
    // and only do it once per conversation
    if (
      messageCount === 1 &&
      !hasTitleBeenGenerated.current &&
      conversationId
    ) {
      hasTitleBeenGenerated.current = true;

      // Request title auto-generation by sending an empty title
      // The backend will generate a title based on the first user message
      updateConversation({
        id: conversationId,
        conversation: { title: "" },
      });
    }
  }, [messageCount, conversationId, updateConversation]);
}
