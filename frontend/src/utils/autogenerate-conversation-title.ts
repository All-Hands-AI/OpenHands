import OpenHands from "#/api/open-hands";
import { queryClient } from "#/query-client-config";

/**
 * Auto-generates the conversation title by sending an empty title to the backend,
 * which triggers auto-generation of a title based on the conversation content.
 *
 * This function will only trigger if the current title does NOT match the pattern
 * "Conversation [a-f0-9]+" (e.g., "Conversation 1a2b3").
 *
 * Uses React Query's invalidation to refresh the data instead of manually fetching.
 *
 * @param conversationId - The ID of the conversation to update
 * @returns A promise that resolves when the title has been updated
 */
export async function autogenerateConversationTitle(
  conversationId: string,
): Promise<void> {
  try {
    // First, get the current conversation to check its title
    const conversation = await OpenHands.getConversation(conversationId);

    if (!conversation) {
      console.error("Conversation not found:", conversationId);
      return;
    }

    // Check if the current title matches the default pattern "Conversation [a-f0-9]+"
    const defaultTitlePattern = /^Conversation [a-f0-9]+$/;

    // Only auto-generate title if it doesn't match the default pattern
    if (conversation.title && !defaultTitlePattern.test(conversation.title)) {
      // Send empty title to trigger auto-generation on the backend
      await OpenHands.updateUserConversation(conversationId, { title: "" });

      // Invalidate the queries to refresh the data
      queryClient.invalidateQueries({
        queryKey: ["user", "conversation", conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });
    }
  } catch (error) {
    console.error("Failed to auto-generate conversation title:", error);

    // Invalidate queries on error
    queryClient.invalidateQueries({
      queryKey: ["user", "conversation", conversationId],
    });
    queryClient.invalidateQueries({
      queryKey: ["user", "conversations"],
    });
  }
}
