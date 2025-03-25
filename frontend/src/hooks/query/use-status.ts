import { useQueryClient } from "@tanstack/react-query";
import { StatusMessage } from "#/types/message";

export function useStatus() {
  const queryClient = useQueryClient();
  return queryClient.getQueryData<StatusMessage>(["_STATE", "status"]);
}