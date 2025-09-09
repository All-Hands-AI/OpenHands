import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";

interface ResetConversationParams {
  conversationId: string;
  deleteOldConversation?: boolean;
}

export const useResetConversation = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({
      conversationId,
      deleteOldConversation = false,
    }: ResetConversationParams) => {
      const response = await fetch(
        `/api/conversations/${conversationId}/reset`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            delete_old_conversation: deleteOldConversation,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to reset conversation");
      }

      return response.json();
    },
    onSuccess: (data) => {
      displaySuccessToast(t(I18nKey.CONVERSATION$RESET_SUCCESS));
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["active-conversation"] });

      // Navigate to the new conversation and close the conversation panel
      if (data.conversation_id) {
        navigate(`/conversations/${data.conversation_id}`, {
          state: { closeConversationPanel: true },
        });
      }
    },
    onError: (error) => {
      displayErrorToast(error.message || t(I18nKey.CONVERSATION$RESET_ERROR));
    },
  });
};
