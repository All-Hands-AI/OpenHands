import { useEffect } from "react";
import { useParams } from "react-router";
import { useSelector, useDispatch } from "react-redux";
import { useQueryClient } from "@tanstack/react-query";
import { useUpdateConversation } from "./mutation/use-update-conversation";
import { RootState } from "#/store";
import { setConversationTitle } from "#/state/conversation-slice";
import OpenHands from "#/api/open-hands";

/**
 * Hook that monitors for the first agent message and triggers title generation.
 * This approach is more robust as it ensures the user message has been processed
 * by the backend and the agent has responded before generating the title.
 */
export function useAutoTitleAfterMessage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const queryClient = useQueryClient();
  const dispatch = useDispatch();
  const { mutate: updateConversation } = useUpdateConversation();

  const messages = useSelector((state: RootState) => state.chat.messages);
  const currentTitle = useSelector(
    (state: RootState) => state.conversation.title,
  );

  useEffect(() => {
    if (!conversationId || !messages || messages.length === 0) {
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
    if (currentTitle && !currentTitle.startsWith("Conversation ")) {
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

            // Update the Redux state with the new title immediately
            if (updatedConversation && updatedConversation.title) {
              dispatch(setConversationTitle(updatedConversation.title));

              // Force update the document title directly as well for immediate feedback
              document.title = `${updatedConversation.title} - OpenHands`;
            }

            // Update the query cache
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
                    conversation.conversation_id === conversationId &&
                    updatedConversation
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
  }, [
    messages,
    conversationId,
    currentTitle,
    updateConversation,
    queryClient,
    dispatch,
  ]);
}
