import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import { useDispatch, useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { setInitialQuery } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { useAuth } from "#/context/auth-context";

export const useCreateConversation = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { gitHubToken } = useAuth();
  const queryClient = useQueryClient();

  const { selectedRepository, files, importedProjectZip } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  return useMutation({
    mutationFn: (variables: { q?: string }) => {
      if (
        !variables.q?.trim() &&
        !selectedRepository &&
        files.length === 0 &&
        !importedProjectZip
      ) {
        throw new Error("No query provided");
      }

      if (variables.q) dispatch(setInitialQuery(variables.q));
      return OpenHands.createConversation(
        gitHubToken || undefined,
        selectedRepository || undefined,
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
