import { useEffect, useRef } from "react";
import { useParams } from "react-router";
import { useSelector } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { useWsClient } from "#/context/ws-client-provider";
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
  const { send } = useWsClient();

  // Track which conversation IDs have already had titles generated
  const generatedTitlesRef = useRef<Set<string>>(new Set());

  // Get messages from the Redux store
  const messages = useSelector((state: RootState) => state.chat.messages);

  // Check for agent messages
  const hasAgentMessage = messages.some(
    (message) => message.sender === "assistant",
  );

  // Debug log to see the current state
  useEffect(() => {
    console.log(
      `[useAutoTitleAfterMessage] Hook called for conversation ${conversationId}`,
    );
    console.log(`[useAutoTitleAfterMessage] Messages:`, messages);
    console.log(
      `[useAutoTitleAfterMessage] Has agent message:`,
      hasAgentMessage,
    );
    console.log(
      `[useAutoTitleAfterMessage] Already generated:`,
      generatedTitlesRef.current.has(conversationId || ""),
    );
  }, [conversationId, messages, hasAgentMessage]);

  // Track when the conversation ID changes
  const lastConversationChangeTime = useRef<number>(Date.now());

  // Reset tracking when the conversation ID changes
  useEffect(() => {
    // This effect runs when the conversation ID changes
    lastConversationChangeTime.current = Date.now();
    console.log(
      `[useAutoTitleAfterMessage] Conversation changed to ${conversationId}, resetting timestamp`,
    );
  }, [conversationId]);

  // Effect to trigger title generation after the first agent message
  useEffect(() => {
    // Check if we have recent messages (after the last conversation change)
    const recentMessages = messages.filter((message) => {
      const messageTime = new Date(message.timestamp).getTime();
      return messageTime > lastConversationChangeTime.current;
    });

    // Check if we have recent agent and user messages
    const hasRecentAgentMessage = recentMessages.some(
      (message) => message.sender === "assistant",
    );
    const hasRecentUserMessage = recentMessages.some(
      (message) => message.sender === "user",
    );

    console.log(`[useAutoTitleAfterMessage] Recent messages:`, recentMessages);
    console.log(
      `[useAutoTitleAfterMessage] Has recent agent message:`,
      hasRecentAgentMessage,
    );
    console.log(
      `[useAutoTitleAfterMessage] Has recent user message:`,
      hasRecentUserMessage,
    );

    // Only proceed if we have a conversation ID, recent agent messages, recent user messages,
    // and haven't generated a title for this conversation yet
    if (
      conversationId &&
      hasRecentAgentMessage &&
      hasRecentUserMessage &&
      !generatedTitlesRef.current.has(conversationId)
    ) {
      // Mark this conversation as having a generated title
      generatedTitlesRef.current.add(conversationId);

      // Debug log to help understand when title generation is triggered
      console.log(
        `[useAutoTitleAfterMessage] Generating title for conversation ${conversationId}`,
      );

      // Generate the title
      updateConversation(
        {
          id: conversationId,
          conversation: { title: "" },
        },
        {
          onSuccess: async () => {
            try {
              // Fetch the updated conversation with the new title
              const updatedConversation =
                await OpenHands.getConversation(conversationId);

              // Update the conversation in the cache directly
              queryClient.setQueryData(
                ["user", "conversation", conversationId],
                updatedConversation,
              );

              // Also update the conversations list cache if it exists
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
              // If direct update fails, fall back to invalidating the query
              queryClient.invalidateQueries({
                queryKey: ["user", "conversation", conversationId],
              });
            }
          },
        },
      );
    }
  }, [messages, conversationId, updateConversation, queryClient]);

  // Return the original send function
  return send;
}
