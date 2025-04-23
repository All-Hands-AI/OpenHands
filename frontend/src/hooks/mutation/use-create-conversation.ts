import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import { useDispatch, useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { setInitialPrompt } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { GitRepository } from "#/types/git";

export const useCreateConversation = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const queryClient = useQueryClient();

  const { selectedRepository, files, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  return useMutation({
    mutationKey: ["create-conversation"],
    mutationFn: async (variables: {
      q?: string;
      selectedRepository?: GitRepository | null;
    }) => {
      if (variables.q) dispatch(setInitialPrompt(variables.q));

      return OpenHands.createConversation(
        variables.selectedRepository || undefined,
        variables.q,
        files,
        replayJson || undefined,
      );
    },
    onSuccess: async ({ conversation_id: conversationId }, { q }) => {
      posthog.capture("initial_query_submitted", {
        entry_point: "task_form",
        query_character_length: q?.length,
        has_repository: !!selectedRepository,
        has_files: files.length > 0,
        has_replay_json: !!replayJson,
      });
      await queryClient.invalidateQueries({
        queryKey: ["user", "conversations"],
      });
      navigate(`/conversations/${conversationId}`);
    },
  });
};
