import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { FeedbackData } from "../query/use-feedback-exists";

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
    onSuccess: (_, { eventId, rating, reason }) => {
      if (eventId) {
        // Update the cache directly instead of invalidating to prevent refetch
        const queryKey = ["feedback", "exists", conversationId, eventId];

        // Update the React Query cache
        queryClient.setQueryData<FeedbackData>(queryKey, {
          exists: true,
          rating,
          reason,
        });

        // Also update the sessionStorage cache
        try {
          const cacheKey = `feedback_${conversationId}_${eventId}`;
          sessionStorage.setItem(
            cacheKey,
            JSON.stringify({ exists: true, rating, reason }),
          );
        } catch (e) {
          // Ignore storage errors
        }
      }
    },
    onError: (error) => {
      // Log error but don't show toast - user will just see the UI stay in unsubmitted state
      // eslint-disable-next-line no-console
      console.error(t("FEEDBACK$FAILED_TO_SUBMIT"), error);
    },
  });
};
