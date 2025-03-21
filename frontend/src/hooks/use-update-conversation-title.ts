import { useParams } from "react-router";
import { updateConversationTitle } from "#/utils/update-conversation-title";

/**
 * Hook that provides a function to update the conversation title.
 * This hook extracts the conversation ID from the URL parameters.
 *
 * @returns A function that can be called to update the conversation title
 */
export function useUpdateConversationTitle(): () => Promise<void> {
  const { conversationId } = useParams<{ conversationId: string }>();

  /**
   * Updates the conversation title for the current conversation
   */
  const updateTitle = async (): Promise<void> => {
    if (!conversationId) {
      return;
    }

    await updateConversationTitle(conversationId);
  };

  return updateTitle;
}
