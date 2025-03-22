import { useMutation } from "@tanstack/react-query";
import { autogenerateConversationTitle } from "#/services/conversation-title-service";

/**
 * Hook for auto-generating a conversation title.
 *
 * This will only trigger if the current title does NOT match the pattern
 * "Conversation [a-f0-9]+" (e.g., "Conversation 1a2b3").
 */
export const useAutogenerateConversationTitle = () =>
  useMutation({
    mutationFn: (conversationId: string) =>
      autogenerateConversationTitle(conversationId),
  });
