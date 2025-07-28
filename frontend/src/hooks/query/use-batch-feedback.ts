import { useQuery, useQueryClient } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useConfig } from "#/hooks/query/use-config";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";

export interface BatchFeedbackData {
  exists: boolean;
  rating?: number;
  reason?: string;
  metadata?: Record<string, unknown>;
}

// Query key factory to ensure consistency across hooks
export const getFeedbackQueryKey = (conversationId?: string) =>
  ["feedback", "data", conversationId] as const;

// Query key factory for individual feedback existence
export const getFeedbackExistsQueryKey = (
  conversationId: string,
  eventId: number,
) => ["feedback", "exists", conversationId, eventId] as const;

export const useBatchFeedback = () => {
  const { conversationId } = useConversationId();
  const { data: config } = useConfig();
  const queryClient = useQueryClient();
  const runtimeIsReady = useRuntimeIsReady();

  return useQuery({
    queryKey: getFeedbackQueryKey(conversationId),
    queryFn: () => OpenHands.getBatchFeedback(conversationId!),
    enabled: runtimeIsReady && !!conversationId && config?.APP_MODE === "saas",
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes,
    select: (data) => {
      // HACK: Using select as a side-effect hook since onSuccess is deprecated
      // This keeps the individual feedback existence cache in sync with batch data
      // Not the intended use of select, but avoids deprecated onSuccess
      Object.entries(data).forEach(([eventId, feedback]) => {
        queryClient.setQueryData(
          getFeedbackExistsQueryKey(conversationId!, parseInt(eventId, 10)),
          feedback.exists,
        );
      });
      return data;
    },
  });
};
