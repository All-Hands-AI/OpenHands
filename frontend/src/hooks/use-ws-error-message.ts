import { useQueryClient } from "@tanstack/react-query";

export const useWSErrorMessage = () => {
  const queryClient = useQueryClient();

  const setErrorMessage = (message: string) => {
    queryClient.setQueryData<string>(["error_message"], message);
  };

  const getErrorMessage = () =>
    queryClient.getQueryData<string>(["error_message"]);

  const removeErrorMessage = () => {
    queryClient.removeQueries({ queryKey: ["error_message"] });
  };

  return {
    setErrorMessage,
    getErrorMessage,
    removeErrorMessage,
  };
};
