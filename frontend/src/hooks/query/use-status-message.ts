import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

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
 * This provides the status slice functionality
 */
export function useStatusMessage() {
  const queryClient = useQueryClient();

  // Get initial state from cache if this is the first time accessing the data
  const getInitialStatusMessage = (): StatusMessage => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<StatusMessage>([
      "status",
      "currentMessage",
    ]);
    if (existingData) return existingData;

    // If no existing data, return the initial state
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
      // eslint-disable-next-line no-console
      console.log("[Status Debug] Setting status message via mutation:", {
        id: statusMessage.id,
        message: statusMessage.message,
        type: statusMessage.type,
      });

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
      // eslint-disable-next-line no-console
      console.error("[Status Debug] Error setting status message");
      // Restore previous status message on error
      if (context?.previousStatusMessage) {
        queryClient.setQueryData(
          ["status", "currentMessage"],
          context.previousStatusMessage,
        );
      }
    },
    onSuccess: (statusMessage) => {
      // eslint-disable-next-line no-console
      console.log("[Status Debug] Successfully set status message:", {
        id: statusMessage.id,
        message: statusMessage.message,
      });
    },
  });

  return {
    statusMessage: query.data || initialStatusMessage,
    isLoading: query.isLoading,
    setStatusMessage: setStatusMessageMutation.mutate,
  };
}
