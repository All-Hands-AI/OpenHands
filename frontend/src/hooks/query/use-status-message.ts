import { useMemo } from "react";
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

  // Use a stable query function to avoid hydration mismatches
  const queryFn = useMemo(
    () => () =>
      queryClient.getQueryData<StatusMessage>(statusMessageQueryKey) ||
      initialStatusMessage,
    [queryClient],
  );

  const { data: curStatusMessage = initialStatusMessage } = useQuery({
    queryKey: statusMessageQueryKey,
    queryFn,
    // We don't want to refetch this data automatically
    staleTime: Infinity,
    gcTime: Infinity,
    // Initialize with the initial status message
    initialData: initialStatusMessage,
  });

  // Use a stable setter function
  const setStatusMessage = useMemo(
    () => (message: StatusMessage) =>
      queryClient.setQueryData(statusMessageQueryKey, message),
    [queryClient],
  );

  return {
    curStatusMessage,
    setStatusMessage,
  };
}
