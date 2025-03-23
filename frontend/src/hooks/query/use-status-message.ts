import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import { StatusMessage } from "#/types/message";

// Initial status message
const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

/**
 * Hook to access and manipulate status messages using React Query
 * This replaces the Redux status slice functionality
 */
export function useStatusMessage() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    console.warn(
      "QueryReduxBridge not initialized, using default status message",
    );
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialStatusMessage = (): StatusMessage => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<StatusMessage>([
      "status",
      "currentMessage",
    ]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<{ curStatusMessage: StatusMessage }>(
          "status",
        ).curStatusMessage;
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialStatusMessage;
      }
    }

    // If bridge is not available, return the initial state
    return initialStatusMessage;
  };

  // Query for status message
  const query = useQuery({
    queryKey: ["status", "currentMessage"],
    queryFn: () => getInitialStatusMessage(),
    initialData: getInitialStatusMessage,
    staleTime: Infinity, // We manage updates manually through mutations
  });

  // Mutation to set current status message
  const setStatusMessageMutation = useMutation({
    mutationFn: (statusMessage: StatusMessage) =>
      Promise.resolve(statusMessage),
    onMutate: async (statusMessage) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["status", "currentMessage"],
      });

      // Get current status message
      const previousStatusMessage = queryClient.getQueryData<StatusMessage>([
        "status",
        "currentMessage",
      ]);

      // Update status message
      queryClient.setQueryData(["status", "currentMessage"], statusMessage);

      return { previousStatusMessage };
    },
    onError: (_, __, context) => {
      // Restore previous status message on error
      if (context?.previousStatusMessage) {
        queryClient.setQueryData(
          ["status", "currentMessage"],
          context.previousStatusMessage,
        );
      }
    },
  });

  return {
    statusMessage: query.data || initialStatusMessage,
    isLoading: query.isLoading,
    setStatusMessage: setStatusMessageMutation.mutate,
  };
}
