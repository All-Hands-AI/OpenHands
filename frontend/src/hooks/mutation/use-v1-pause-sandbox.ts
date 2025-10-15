import { useMutation, useQueryClient } from "@tanstack/react-query";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";

export const useV1PauseSandbox = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (variables: { sandboxId: string }) =>
      V1ConversationService.pauseSandbox(variables.sandboxId),
    onSuccess: (_, variables) => {
      // Invalidate sandbox queries to trigger automatic refetch
      queryClient.invalidateQueries({
        queryKey: ["sandboxes", variables.sandboxId],
      });
      // Also invalidate the sandboxes list
      queryClient.invalidateQueries({ queryKey: ["sandboxes"] });
    },
  });
};
