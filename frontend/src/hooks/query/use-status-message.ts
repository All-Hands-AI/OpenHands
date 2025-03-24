import { useQuery, useQueryClient } from "@tanstack/react-query";

import { StatusMessage } from "#/types/message";

const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

export const STATUS_QUERY_KEY = ["status", "currentMessage"];

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

export function useStatusMessage() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: STATUS_QUERY_KEY,
    queryFn: () => {
      const existingData =
        queryClient.getQueryData<StatusMessage>(STATUS_QUERY_KEY);
      if (existingData) return existingData;
      return initialStatusMessage;
    },
    initialData: initialStatusMessage,
    staleTime: Infinity,
  });

  const setStatusMessage = (newStatusMessage: StatusMessage) => {
    setAgentStatus(queryClient, newStatusMessage);
  };

  return {
    statusMessage: query.data || initialStatusMessage,
    isLoading: query.isLoading,
    setStatusMessage,
  };
}
