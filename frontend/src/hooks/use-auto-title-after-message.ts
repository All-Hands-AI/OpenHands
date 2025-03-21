import { useEffect, useRef } from "react";
import { useParams } from "react-router";
import { useSelector } from "react-redux";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { useWsClient } from "#/context/ws-client-provider";
import { RootState } from "#/store";

/**
 * Hook that monitors for the first agent message and triggers title generation.
 * This approach is more robust as it ensures the user message has been processed
 * by the backend and the agent has responded before generating the title.
 *
 * @returns The original WebSocket send function
 */
export function useAutoTitleAfterMessage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { mutate: updateConversation } = useUpdateConversation();
  const { send } = useWsClient();
  const hasTitleBeenGenerated = useRef(false);

  // Get messages from the Redux store
  const messages = useSelector((state: RootState) => state.chat.messages);

  // Check for agent messages
  const hasAgentMessage = messages.some(
    (message) => message.sender === "assistant",
  );

  // Effect to trigger title generation after the first agent message
  useEffect(() => {
    if (hasAgentMessage && !hasTitleBeenGenerated.current && conversationId) {
      console.log(
        "[useAutoTitleAfterMessage] First agent message detected, generating title",
      );
      hasTitleBeenGenerated.current = true;

      // Generate the title
      updateConversation({
        id: conversationId,
        conversation: { title: "" },
      });
      console.log("[useAutoTitleAfterMessage] Title generation request sent");
    }
  }, [hasAgentMessage, conversationId, updateConversation]);

  // Return the original send function
  return send;
}
