import { useEffect } from "react";
import { useParams } from "react-router";
import { useSelector, useDispatch } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { RootState } from "#/store";
import OpenHands from "#/api/open-hands";
import { useUserConversation } from "#/hooks/query/use-user-conversation";
import { useParams } from "react-router";

/**
 * Hook that monitors for the first agent message and triggers title generation.
 * This approach is more robust as it ensures the user message has been processed
 * by the backend and the agent has responded before generating the title.
 */
export function useAutoTitle() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: conversation, isFetched } = useUserConversation(
    conversationId ?? null,
  );
  const queryClient = useQueryClient();
  const dispatch = useDispatch();
  const { mutate: updateConversation } = useUpdateConversation();

  const messages = useSelector((state: RootState) => state.chat.messages);

  useEffect(() => {
    if (!conversation || !conversationId || !messages || messages.length === 0) {
      return;
    }

    const hasAgentMessage = messages.some(
      (message) => message.sender === "assistant",
    );
    const hasUserMessage = messages.some(
      (message) => message.sender === "user",
    );

    if (!hasAgentMessage || !hasUserMessage) {
      return;
    }

    // Skip if we already have a meaningful title (not the default "Conversation" prefix)
    if (conversation.title && !conversation.title.startsWith("Conversation ")) {
      return;
    }

    updateConversation(
      {
        id: conversationId,
        conversation: { title: "" },
      },
      {
        onSuccess: async () => {
          try {
            const updatedConversation =
              await OpenHands.getConversation(conversationId);

            queryClient.setQueryData(
              ["user", "conversation", conversationId],
              updatedConversation,
            );
          } catch (error) {
            queryClient.invalidateQueries({
              queryKey: ["user", "conversation", conversationId],
            });
          }
        },
      },
    );
  }, [
    messages,
    conversationId,
    conversation,
    updateConversation,
    queryClient,
    dispatch,
  ]);
}
