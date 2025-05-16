import { useQueryClient } from "@tanstack/react-query";

export const useOptimisticUserMessage = () => {
  const queryKey = ["optimistic_user_message"] as const;
  const queryClient = useQueryClient();

  const setOptimisticUserMessage = (message: string) => {
    queryClient.setQueryData<string>(queryKey, message);
  };

  const getOptimisticUserMessage = () =>
    queryClient.getQueryData<string>(queryKey);

  const removeOptimisticUserMessage = () => {
    queryClient.removeQueries({ queryKey });
  };

  return {
    setOptimisticUserMessage,
    getOptimisticUserMessage,
    removeOptimisticUserMessage,
  };
};
