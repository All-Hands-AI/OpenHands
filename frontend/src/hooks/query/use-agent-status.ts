import { useQueryClient } from "@tanstack/react-query";
import { StatusMessage } from "#/types/message";

// Query key for status messages
const STATUS_QUERY_KEY = ["_STATE", "status"];

/**
 * Sets the agent status message in the query cache
 * @param queryClient - The React Query client
 * @param statusMessage - The status message to set
 */
export function setAgentStatus(
  queryClient: ReturnType<typeof useQueryClient>,
  statusMessage: StatusMessage,
) {
  queryClient.setQueryData(STATUS_QUERY_KEY, statusMessage);
}

/**
 * Hook to access and manage agent status messages
 * @returns Object containing the current status message and a setter function
 */
export function useAgentStatus(): {
  statusMessage: StatusMessage | undefined;
  setStatusMessage: (statusMessage: StatusMessage) => void;
} {
  const queryClient = useQueryClient();

  // Get the current status message from the query cache
  const statusMessage =
    queryClient.getQueryData<StatusMessage>(STATUS_QUERY_KEY);

  // Create a setter function that components can use
  const setStatusMessage = (newStatusMessage: StatusMessage) => {
    setAgentStatus(queryClient, newStatusMessage);
  };

  return {
    statusMessage,
    setStatusMessage,
  };
}
