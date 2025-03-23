import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useInitialQuery } from "#/hooks/query/use-initial-query";

export const useCreateConversation = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectedRepository, files, setInitialPrompt } = useInitialQuery();

  return useMutation({
    mutationFn: async (variables: { q?: string }) => {
      if (variables.q) setInitialPrompt(variables.q);

      // Get the latest state directly from the query client
      const latestState = queryClient.getQueryData<{
        files: string[];
        initialPrompt: string | null;
        selectedRepository: string | null;
      }>(["initialQuery"]);

      const latestRepository =
        latestState?.selectedRepository || selectedRepository;

      // Use the latest repository from the query client

      return OpenHands.createConversation(
        latestRepository || undefined,
        variables.q,
        files,
      );
    },
    onSuccess: async ({ conversation_id: conversationId }, { q }) => {
      // Get the latest state again for analytics
      const latestState = queryClient.getQueryData<{
        files: string[];
        initialPrompt: string | null;
        selectedRepository: string | null;
      }>(["initialQuery"]);

      const latestRepository =
        latestState?.selectedRepository || selectedRepository;

      posthog.capture("initial_query_submitted", {
        entry_point: "task_form",
        query_character_length: q?.length,
        has_repository: !!latestRepository,
        has_files: files.length > 0,
      });
      await queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });
      navigate(`/conversations/${conversationId}`);
    },
  });
};
