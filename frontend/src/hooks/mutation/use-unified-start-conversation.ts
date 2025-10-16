import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Provider } from "#/types/settings";
import { useErrorMessageStore } from "#/stores/error-message-store";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";
import {
  getConversationVersionFromQueryCache,
  startV1Conversation,
  startV0Conversation,
  updateConversationStatusInCache,
  invalidateConversationQueries,
} from "./conversation-mutation-utils";

/**
 * Unified hook that automatically routes to the correct start conversation implementation
 * based on the conversation version (V0 or V1).
 *
 * This hook checks the cached conversation data to determine the version, then calls
 * the appropriate API directly. Returns a single useMutation instance that all components share.
 *
 * Usage is the same as useStartConversation:
 * const { mutate: startConversation } = useUnifiedStartConversation();
 * startConversation({ conversationId: "some-id", providers: [...] });
 */
export const useUnifiedStartConversation = () => {
  const queryClient = useQueryClient();
  const removeErrorMessage = useErrorMessageStore(
    (state) => state.removeErrorMessage,
  );

  return useMutation({
    mutationKey: ["start-conversation"],
    mutationFn: async (variables: {
      conversationId: string;
      providers?: Provider[];
    }) => {
      const version = getConversationVersionFromQueryCache(
        queryClient,
        variables.conversationId,
      );

      if (version === "V1") {
        return startV1Conversation(variables.conversationId);
      }

      return startV0Conversation(variables.conversationId, variables.providers);
    },
    onMutate: async () => {
      toast.loading("Starting conversation...", TOAST_OPTIONS);

      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      return { previousConversations };
    },
    onError: (_, __, context) => {
      toast.dismiss();
      toast.error("Failed to start conversation", TOAST_OPTIONS);

      if (context?.previousConversations) {
        queryClient.setQueryData(
          ["user", "conversations"],
          context.previousConversations,
        );
      }
    },
    onSettled: (_, __, variables) => {
      invalidateConversationQueries(queryClient, variables.conversationId);
    },
    onSuccess: (_, variables) => {
      toast.dismiss();
      toast.success("Conversation started", TOAST_OPTIONS);

      // Clear error messages when starting/resuming conversation
      removeErrorMessage();

      updateConversationStatusInCache(
        queryClient,
        variables.conversationId,
        "RUNNING",
      );
    },
  });
};
