import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

interface GetTrajectorySummaryParams {
  conversationId: string;
  lastSummarizedId?: number | null;
}

export const useGetTrajectorySummary = () =>
  useMutation({
    mutationFn: (params: GetTrajectorySummaryParams | string) => {
      // Support both the new object format and the old string format for backward compatibility
      if (typeof params === 'string') {
        return OpenHands.getTrajectorySummary(params);
      } else {
        const { conversationId, lastSummarizedId } = params;
        return OpenHands.getTrajectorySummary(conversationId, lastSummarizedId);
      }
    },
  });
