import { useEffect, useRef } from "react";
import { useParams } from "react-router";
import { useSelector } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { RootState } from "#/store";
import OpenHands from "#/api/open-hands";

/**
 * Hook that monitors for the first agent message and triggers title generation.
 * This approach is more robust as it ensures the user message has been processed
 * by the backend and the agent has responded before generating the title.
 *
 * @returns The original WebSocket send function
 */
export function useAutoTitleAfterMessage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const queryClient = useQueryClient();
  const { mutate: updateConversation } = useUpdateConversation();

  const generatedTitlesRef = useRef<Set<string>>(new Set());

  const messages = useSelector((state: RootState) => state.chat.messages);

  useEffect(() => {
    const hasAgentMessage = messages.some(
      (message) => message.sender === "assistant",
    );
    const hasUserMessage = messages.some(
      (message) => message.sender === "user",
    );

    console.log('triggering', hasAgentMessage, hasUserMessage, conversationId, generatedTitlesRef.current.has(conversationId));

    if (
      hasAgentMessage &&
      hasUserMessage &&
      conversationId &&
      !generatedTitlesRef.current.has(conversationId)
    ) {
      generatedTitlesRef.current.add(conversationId);

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

              queryClient.setQueriesData(
                { queryKey: ["user", "conversations"] },
                (oldData: unknown) => {
                  if (!oldData) return oldData;

                  return (oldData as Array<{ conversation_id: string }>).map(
                    (conversation) =>
                      conversation.conversation_id === conversationId
                        ? { ...conversation, title: updatedConversation.title }
                        : conversation,
                  );
                },
              );
            } catch (error) {
              queryClient.invalidateQueries({
                queryKey: ["user", "conversation", conversationId],
              });
            }
          },
        },
      );
    }
  }, [messages, conversationId, updateConversation, queryClient]);
}
