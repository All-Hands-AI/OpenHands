import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { Provider } from "#/types/settings";
import { useErrorMessageStore } from "#/stores/error-message-store";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";
import {
  getConversationVersionFromQueryCache,
  resumeV1ConversationSandbox,
  startV0Conversation,
  updateConversationStatusInCache,
  invalidateConversationQueries,
} from "./conversation-mutation-utils";

/**
 * Unified hook that automatically routes to the correct resume conversation sandbox implementation
 * based on the conversation version (V0 or V1).
 *
 * This hook checks the cached conversation data to determine the version, then calls
 * the appropriate API directly. Returns a single useMutation instance that all components share.
 *
 * Usage is the same as useStartConversation:
 * const { mutate: startConversation } = useUnifiedResumeConversationSandbox();
 * startConversation({ conversationId: "some-id", providers: [...] });
 */
export const useUnifiedResumeConversationSandbox = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const removeErrorMessage = useErrorMessageStore(
    (state) => state.removeErrorMessage,
  );

  return useMutation({
    mutationKey: ["start-conversation"],
    mutationFn: async (variables: {
      conversationId: string;
      providers?: Provider[];
      version?: "V0" | "V1";
    }) => {
      // Use provided version or fallback to cache lookup
      const version =
        variables.version ||
        getConversationVersionFromQueryCache(
          queryClient,
          variables.conversationId,
        );

      if (version === "V1") {
        return resumeV1ConversationSandbox(variables.conversationId);
      }

      return startV0Conversation(variables.conversationId, variables.providers);
    },
    onMutate: async () => {
      const toastId = toast.loading(
        t(I18nKey.TOAST$STARTING_CONVERSATION),
        TOAST_OPTIONS,
      );

      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      return { previousConversations, toastId };
    },
    onError: (_, __, context) => {
      if (context?.toastId) {
        toast.dismiss(context.toastId);
      }
      toast.error(t(I18nKey.TOAST$FAILED_TO_START_CONVERSATION), TOAST_OPTIONS);

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
    onSuccess: (_, variables, context) => {
      if (context?.toastId) {
        toast.dismiss(context.toastId);
      }
      toast.success(t(I18nKey.TOAST$CONVERSATION_STARTED), TOAST_OPTIONS);

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
