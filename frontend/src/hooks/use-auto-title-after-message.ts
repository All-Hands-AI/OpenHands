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
      hasTitleBeenGenerated.current = true;

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
              const updatedConversation = await OpenHands.getConversation(conversationId);
              
              // Update the conversation in the cache directly
              queryClient.setQueryData(
                ["user", "conversation", conversationId],
                updatedConversation
              );
              
              // Also update the conversations list cache if it exists
              queryClient.setQueriesData(
                { queryKey: ["user", "conversations"] },
                (oldData: any) => {
                  if (!oldData) return oldData;
                  
                  return oldData.map((conversation: any) => 
                    conversation.conversation_id === conversationId
                      ? { ...conversation, title: updatedConversation.title }
                      : conversation
                  );
                }
              );
            } catch (error) {
              // If direct update fails, fall back to invalidating the query
              queryClient.invalidateQueries({ 
                queryKey: ["user", "conversation", conversationId] 
              });
            }
          },
        },
      );
    }
  }, [hasAgentMessage, conversationId, updateConversation, queryClient]);

  // Return the original send function
  return send;
}
