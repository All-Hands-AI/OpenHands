import { useQuery, useQueryClient } from "@tanstack/react-query";

import { StatusMessage } from "#/types/message";

// Initial status message
const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

// Query key for status message
export const STATUS_QUERY_KEY = ["status", "currentMessage"];

/**
 * Helper function to set agent status
 */
export function setAgentStatus(
  queryClient: ReturnType<typeof useQueryClient>,
  statusMessage: StatusMessage,
) {
  // eslint-disable-next-line no-console
  console.log("[Status Debug] Setting status message:", {
    id: statusMessage.id,
    message: statusMessage.message,
    type: statusMessage.type,
  });

  queryClient.setQueryData(STATUS_QUERY_KEY, statusMessage);
}

/**
 * Hook to access and manipulate status messages using React Query
 * This provides the status slice functionality
 */
export function useStatusMessage() {
  const queryClient = useQueryClient();

  // Query for status message
  const query = useQuery({
    queryKey: STATUS_QUERY_KEY,
    queryFn: () => {
      // If we already have data in React Query, use that
      const existingData =
        queryClient.getQueryData<StatusMessage>(STATUS_QUERY_KEY);
      if (existingData) return existingData;

      // If no existing data, return the initial state
      return initialStatusMessage;
    },
    initialData: initialStatusMessage,
    staleTime: Infinity, // We manage updates manually
  });

  // Create a setter function that components can use
  const setStatusMessage = (newStatusMessage: StatusMessage) => {
    setAgentStatus(queryClient, newStatusMessage);
  };

  return {
    statusMessage: query.data || initialStatusMessage,
    isLoading: query.isLoading,
    setStatusMessage,
  };
}
