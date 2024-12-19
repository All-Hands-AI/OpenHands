import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router";
import OpenHands from "#/api/open-hands";

export const useCreateConversation = () => {
  const [, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: OpenHands.createConversation,
    onSuccess: async (data) => {
      setSearchParams({ cid: data.id });
      await queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });
    },
  });
};
