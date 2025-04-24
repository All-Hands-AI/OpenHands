import { useEffect } from "react";
import { useParams } from "react-router";
import { useSelector, useDispatch } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { RootState } from "#/store";
import OpenHands from "#/api/open-hands";
import { useUserConversation } from "#/hooks/query/use-user-conversation";

const defaultTitlePattern = /^Conversation [a-f0-9]+$/;

/**
 * Hook that monitors for the first agent message and triggers title generation.
 * This approach is more robust as it ensures the user message has been processed
 * by the backend and the agent has responded before generating the title.
 */
export function useAutoTitle() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: conversation } = useUserConversation(conversationId ?? null);
  const queryClient = useQueryClient();
  const dispatch = useDispatch();
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

    if (!hasAgentMessage || !hasUserMessage) {
      return;
    }

    if (conversation.title && !defaultTitlePattern.test(conversation.title)) {
      return;
    }

    // Request title generation from the backend
    updateConversation(
      {
        id: conversationId,
        conversation: { title: "" },
      },
      {
        onSuccess: async () => {
          try {
            // Add a small delay to allow the backend to generate the title
            // This helps avoid race conditions where we fetch before the title is ready
            setTimeout(async () => {
              try {
                const updatedConversation =
                  await OpenHands.getConversation(conversationId);

                if (updatedConversation && updatedConversation.title) {
                  queryClient.setQueryData(
                    ["user", "conversation", conversationId],
                    updatedConversation,
                  );
                } else {
                  // If we still don't have a title, invalidate the query to trigger a refetch
                  queryClient.invalidateQueries({
                    queryKey: ["user", "conversation", conversationId],
                  });
                }
              } catch (error) {
                queryClient.invalidateQueries({
                  queryKey: ["user", "conversation", conversationId],
                });
              }
            }, 1000); // 1 second delay
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
