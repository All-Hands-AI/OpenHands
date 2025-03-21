import OpenHands from "#/api/open-hands";
import { queryClient } from "#/query-client-config";

/**
 * Updates the conversation title by sending an empty title to the backend,
 * which triggers auto-generation of a title based on the conversation content.
 *
 * Uses React Query's invalidation to refresh the data instead of manually fetching.
 *
 * @param conversationId - The ID of the conversation to update
 * @returns A promise that resolves when the title has been updated
 */
export async function updateConversationTitle(
  conversationId: string,
): Promise<void> {
  try {
    // Send empty title to trigger auto-generation on the backend
    await OpenHands.updateUserConversation(conversationId, { title: "" });

    // Invalidate the queries to refresh the data
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
    queryClient.invalidateQueries({
      queryKey: ["user", "conversations"],
    });
  } catch (error) {
    console.error("Failed to update conversation title:", error);

    // Invalidate queries on error
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
    queryClient.invalidateQueries({
      queryKey: ["user", "conversations"],
    });
  }
}
