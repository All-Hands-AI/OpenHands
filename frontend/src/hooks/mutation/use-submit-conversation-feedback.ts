import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";

type SubmitConversationFeedbackArgs = {
  rating: number;
  eventId?: number;
  reason?: string;
};

export const useSubmitConversationFeedback = () => {
  const { conversationId } = useConversationId();
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: ({ rating, eventId, reason }: SubmitConversationFeedbackArgs) =>
      OpenHands.submitConversationFeedback(
        conversationId,
        rating,
        eventId,
        reason,
      ),
    onSuccess: (_, { eventId }) => {
      // Invalidate the feedback existence query to trigger a refetch
      if (eventId) {
        queryClient.invalidateQueries({
          queryKey: ["feedback", "exists", conversationId, eventId],
        });
      }
    },
    onError: (error) => {
      // Log error but don't show toast - user will just see the UI stay in unsubmitted state
      // eslint-disable-next-line no-console
      console.error(t("FEEDBACK$FAILED_TO_SUBMIT"), error);
    },
  });
};
