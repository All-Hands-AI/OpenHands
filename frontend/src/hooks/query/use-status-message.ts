import { useQueryClient, useQuery } from "@tanstack/react-query";
import { StatusMessage } from "#/types/message";

const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

export const statusMessageQueryKey = ["statusMessage"];

export function useStatusMessage() {
  const queryClient = useQueryClient();

  const { data: curStatusMessage = initialStatusMessage } = useQuery({
    queryKey: statusMessageQueryKey,
    queryFn: () =>
      queryClient.getQueryData<StatusMessage>(statusMessageQueryKey) ||
      initialStatusMessage,
    // We don't want to refetch this data automatically
    staleTime: Infinity,
    gcTime: Infinity,
    // Initialize with the initial status message
    initialData: initialStatusMessage,
  });

  const setStatusMessage = (message: StatusMessage) =>
    queryClient.setQueryData(statusMessageQueryKey, message);

  return {
    curStatusMessage,
    setStatusMessage,
  };
}
