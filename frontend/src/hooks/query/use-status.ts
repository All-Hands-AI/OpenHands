import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { StatusMessage } from "#/types/message";

const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

// Define query keys
export const statusKeys = {
  all: ["status"] as const,
  current: () => [...statusKeys.all, "current"] as const,
};

// Custom hook to get and update status message
export function useStatusMessage() {
  const queryClient = useQueryClient();

  // Query to get the current status message
  const query = useQuery({
    queryKey: statusKeys.current(),
    queryFn: () =>
      // Return the cached value or initial value
      queryClient.getQueryData<StatusMessage>(statusKeys.current()) ||
      initialStatusMessage,
    // Initialize with the default status message
    initialData: initialStatusMessage,
  });

  // Mutation to update the status message
  const mutation = useMutation({
    mutationFn: (newStatusMessage: StatusMessage) =>
      Promise.resolve(newStatusMessage),
    onSuccess: (newStatusMessage) => {
      queryClient.setQueryData(statusKeys.current(), newStatusMessage);
    },
  });

  return {
    statusMessage: query.data,
    setStatusMessage: mutation.mutate,
    isLoading: query.isLoading,
  };
}
