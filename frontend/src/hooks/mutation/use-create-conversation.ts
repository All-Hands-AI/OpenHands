import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useFileStateContext } from "#/context/file-state-context";

export const useCreateConversation = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectedRepository, files } = useFileStateContext();

  return useMutation({
    mutationFn: async (variables: { q?: string }) =>
      OpenHands.createConversation(
        selectedRepository || undefined,
        variables.q,
        files,
      ),
    onSuccess: async ({ conversation_id: conversationId }, { q }) => {
      posthog.capture("initial_query_submitted", {
        entry_point: "task_form",
        query_character_length: q?.length,
        has_repository: !!selectedRepository,
        has_files: files.length > 0,
      });
      await queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });
      navigate(`/conversations/${conversationId}`);
    },
  });
};
