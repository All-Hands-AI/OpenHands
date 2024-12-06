import { useQueryClient, useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { Conversation } from "#/api/open-hands.types";

export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: {
      id: string;
      project: Partial<Omit<Conversation, "id">>;
    }) => OpenHands.updateUserConversation(variables.id, variables.project),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
};
