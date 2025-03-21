import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router";
import { useSelector } from "react-redux";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { RootState } from "#/store";

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
  const [previousMessageCount, setPreviousMessageCount] = useState(0);

  // Get the actual messages to check if there's a user message
  const messages = useSelector((state: RootState) => state.chat.messages);
  const hasUserMessage = messages.some((message) => message.sender === "user");

  useEffect(() => {
    console.log("[useAutoGenerateTitle] Effect triggered:", {
      messageCount,
      previousMessageCount,
      conversationId,
      hasTitleBeenGenerated: hasTitleBeenGenerated.current,
      hasUserMessage,
      messages: messages.map((m) => ({
        sender: m.sender,
        content: m.content.substring(0, 20),
      })),
    });

    // Only trigger title generation after a user message has been added
    // and only do it once per conversation
    if (
      messageCount > previousMessageCount && // Message count increased
      hasUserMessage && // There's at least one user message
      !hasTitleBeenGenerated.current && // We haven't generated a title yet
      conversationId // We have a conversation ID
    ) {
      console.log("[useAutoGenerateTitle] Conditions met, generating title");
      hasTitleBeenGenerated.current = true;

      // Add a small delay to ensure the message has been processed by the backend
      setTimeout(() => {
        // Request title auto-generation by sending an empty title
        // The backend will generate a title based on the first user message
        updateConversation({
          id: conversationId,
          conversation: { title: "" },
        });
        console.log("[useAutoGenerateTitle] Title generation request sent");
      }, 1000);
    }

    setPreviousMessageCount(messageCount);
  }, [
    messageCount,
    conversationId,
    updateConversation,
    hasUserMessage,
    messages,
    previousMessageCount,
  ]);
}
