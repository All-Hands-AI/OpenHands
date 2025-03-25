import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { StatusMessage } from "#/types/message";

const STATUS_MESSAGE_KEY = ["_STATE", "status"];

export const useStatusMessage = () => {
  const queryClient = useQueryClient();

  const setStatusMessage = React.useCallback(
    (status: StatusMessage) => {
      queryClient.setQueryData<StatusMessage>(STATUS_MESSAGE_KEY, status);
    },
    [queryClient],
  );

  const statusMessage =
    queryClient.getQueryData<StatusMessage>(STATUS_MESSAGE_KEY);

  return { statusMessage, setStatusMessage };
};
