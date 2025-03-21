import { QueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { setConversationTitle } from "#/state/conversation-slice";
import store from "#/store";

/**
 * Updates the conversation title by sending an empty title to the backend,
 * which triggers auto-generation of a title based on the conversation content.
 *
 * @param conversationId - The ID of the conversation to update
 * @returns A promise that resolves when the title has been updated
 */
export async function updateConversationTitle(
  conversationId: string,
): Promise<void> {
  // Skip if we already have a meaningful title (not the default "Conversation" prefix)
  const currentTitle = store.getState().conversation.title;
  if (currentTitle && !currentTitle.startsWith("Conversation ")) {
    return;
  }

  try {
    // Create a query client for cache invalidation
    const queryClient = new QueryClient();

    // Send empty title to trigger auto-generation on the backend
    await OpenHands.updateUserConversation(conversationId, { title: "" });

    // Fetch the updated conversation with the new title
    const updatedConversation = await OpenHands.getConversation(conversationId);

    // Update the Redux state with the new title
    if (updatedConversation && updatedConversation.title) {
      store.dispatch(setConversationTitle(updatedConversation.title));

      // Update document title
      document.title = `${updatedConversation.title} - OpenHands`;

      // Update the query cache
      queryClient.setQueryData(
        ["user", "conversation", conversationId],
        updatedConversation,
      );

      // Update the conversations list in the cache
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
    }
  } catch (error) {
    console.error("Failed to update conversation title:", error);

    // Create a query client for cache invalidation on error
    const queryClient = new QueryClient();

    // Invalidate queries on error
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
    queryClient.invalidateQueries({
      queryKey: ["user", "conversations"],
    });
  }
}
