import { useMutation, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import {
  BatchFeedbackData,
  getFeedbackQueryKey,
} from "../query/use-batch-feedback";

type SubmitConversationFeedbackArgs = {
  rating: number;
  eventId?: number;
  reason?: string;
};

export const useSubmitConversationFeedback = () => {
  const { conversationId } = useConversationId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ rating, eventId, reason }: SubmitConversationFeedbackArgs) =>
      OpenHands.submitConversationFeedback(
        conversationId,
        rating,
        eventId,
        reason,
      ),
    onMutate: async ({ rating, eventId, reason }) => {
      if (!eventId) return { previousFeedback: null };

      // Get the query key for the feedback data
      const queryKey = getFeedbackQueryKey(conversationId);

      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot the previous value
      const previousFeedback =
        queryClient.getQueryData<Record<string, BatchFeedbackData>>(queryKey);

      // Optimistically update the cache
      queryClient.setQueryData<Record<string, BatchFeedbackData>>(
        queryKey,
        (old = {}) => {
          const newData = { ...old };
          newData[eventId.toString()] = {
            exists: true,
            rating,
            reason,
            metadata: { source: "likert-scale" },
          };
          return newData;
        },
      );

      // Return a context object with the snapshotted value
      return { previousFeedback };
    },
    onError: (error, { eventId }, context) => {
      // Roll back to the previous value on error
      if (context?.previousFeedback && eventId) {
        queryClient.setQueryData(
          getFeedbackQueryKey(conversationId),
          context.previousFeedback,
        );
      }
      // Log error but don't show toast - user will just see the UI stay in unsubmitted state
      // eslint-disable-next-line no-console
      console.error(error);
    },
    onSettled: (_, __, { eventId }) => {
      if (eventId) {
        // Invalidate both the old and new query keys to ensure consistency
        queryClient.invalidateQueries({
          queryKey: getFeedbackQueryKey(conversationId),
        });
      }
    },
  });
};
