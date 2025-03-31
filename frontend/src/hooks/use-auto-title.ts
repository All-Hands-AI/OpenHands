import { useEffect } from "react";
import { useParams } from "react-router";
import { useSelector } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { RootState } from "#/store";
import { useUserConversation } from "#/hooks/query/use-user-conversation";

/**
 * Hook that monitors for the first agent message and triggers title generation.
 * This approach is more robust as it ensures the user message has been processed
 * by the backend and the agent has responded before generating the title.
 */
export function useAutoTitle() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: conversation } = useUserConversation(conversationId ?? null);
  const queryClient = useQueryClient();
  const { mutate: updateConversation } = useUpdateConversation();

  const messages = useSelector((state: RootState) => state.chat.messages);

  useEffect(() => {
    if (
      !conversation ||
      !conversationId ||
      !messages ||
      messages.length === 0
    ) {
      return;
    }

    const hasAgentMessage = messages.some(
      (message) => message.sender === "assistant",
    );
    const hasUserMessage = messages.some(
      (message) => message.sender === "user",
    );

    // Check if we need to update the title
    if (!hasAgentMessage || !hasUserMessage) {
      return;
    }

    // If the conversation needs a title update or has a default title
    if (conversation.needs_title_update) {
      // Use the PATCH endpoint to update the title
      updateConversation(
        {
          id: conversationId,
          conversation: { title: "" },
        },
        {
          onSuccess: () => {
            // Invalidate the query to refresh the conversation data
            queryClient.invalidateQueries({
              queryKey: ["user", "conversation", conversationId],
            });
          },
        },
      );
    }
  }, [
    messages,
    conversationId,
    conversation,
    updateConversation,
    queryClient,
  ]);
}
