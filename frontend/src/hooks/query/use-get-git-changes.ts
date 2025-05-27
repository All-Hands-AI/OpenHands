import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { GitChange } from "#/api/open-hands.types";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";

export const useGetGitChanges = () => {
  const { conversationId } = useConversationId();
  const [orderedChanges, setOrderedChanges] = React.useState<GitChange[]>([]);
  const previousDataRef = React.useRef<GitChange[]>(null);
  const runtimeIsReady = useRuntimeIsReady();

  const result = useQuery({
    queryKey: ["file_changes", conversationId],
    queryFn: () => OpenHands.getGitChanges(conversationId),
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    enabled: runtimeIsReady && !!conversationId,
    meta: {
      disableToast: true,
    },
  });

  // Latest changes should be on top
  React.useEffect(() => {
    if (!result.isFetching && result.isSuccess && result.data) {
      const currentData = result.data;

      // If this is new data (not the same reference as before)
      if (currentData !== previousDataRef.current) {
        previousDataRef.current = currentData;

        // Figure out new items by comparing with what we already have
        if (Array.isArray(currentData)) {
          const currentIds = new Set(currentData.map((item) => item.path));
          const existingIds = new Set(orderedChanges.map((item) => item.path));

          // Filter out items that already exist in orderedChanges
          const newItems = currentData.filter(
            (item) => !existingIds.has(item.path),
          );

          // Filter out items that no longer exist in the API response
          const existingItems = orderedChanges.filter((item) =>
            currentIds.has(item.path),
          );

          // Add new items to the beginning
          setOrderedChanges([...newItems, ...existingItems]);
        } else {
          // If not an array, just use the data directly
          setOrderedChanges([currentData]);
        }
      }
    }
  }, [result.isFetching, result.isSuccess, result.data]);

  return {
    data: orderedChanges,
    isLoading: result.isLoading,
    isSuccess: result.isSuccess,
    isError: result.isError,
    error: result.error,
  };
};
