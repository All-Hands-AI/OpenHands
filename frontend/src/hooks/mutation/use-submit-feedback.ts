import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Feedback } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { BatchFeedbackData, getFeedbackQueryKey } from "../query/use-batch-feedback";

type SubmitFeedbackArgs = {
  feedback: Feedback;
};

export const useSubmitFeedback = () => {
  const { conversationId } = useConversationId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ feedback }: SubmitFeedbackArgs) =>
      OpenHands.submitFeedback(conversationId, feedback),
    onMutate: async ({ feedback }) => {
      if (!feedback.event_id) return;

      // Get the query key for the feedback data
      const queryKey = getFeedbackQueryKey(conversationId);

      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot the previous value
      const previousFeedback = queryClient.getQueryData<Record<string, BatchFeedbackData>>(queryKey);

      // Optimistically update the cache
      queryClient.setQueryData<Record<string, BatchFeedbackData>>(queryKey, (old) => {
        const newData = { ...old };
        newData[feedback.event_id!.toString()] = {
          exists: true,
          rating: feedback.rating,
          reason: feedback.reason,
          metadata: feedback.metadata,
        };
        return newData;
      });

      // Return a context object with the snapshotted value
      return { previousFeedback };
    },
    onError: (error, variables, context) => {
      // On error, roll back to the previous value
      if (context?.previousFeedback) {
        queryClient.setQueryData(getFeedbackQueryKey(conversationId), context.previousFeedback);
      }
      displayErrorToast(error.message);
    },
    onSettled: () => {
      // Invalidate the query to ensure we're eventually consistent
      queryClient.invalidateQueries({ queryKey: getFeedbackQueryKey(conversationId) });
    },
    retry: 2,
    retryDelay: 500,
  });
};
