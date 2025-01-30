import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import { useDispatch, useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { setInitialPrompt } from "#/state/initial-query-slice";
import { RootState } from "#/store";

export const useCreateConversation = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const queryClient = useQueryClient();

  const { selectedRepository, files, importedProjectZip } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  return useMutation({
    mutationFn: async (variables: { q?: string }) => {
      if (
        !variables.q?.trim() &&
        !selectedRepository &&
        files.length === 0 &&
        !importedProjectZip
      ) {
        throw new Error("No query provided");
      }

      if (variables.q) dispatch(setInitialPrompt(variables.q));

      return OpenHands.createConversation(
        selectedRepository || undefined,
        variables.q,
        files,
      );
    },
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
