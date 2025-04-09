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

  const { selectedRepository, files, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  return useMutation({
    mutationFn: async (variables: { q?: string }) => {
      if (
        !variables.q?.trim() &&
        !selectedRepository &&
        files.length === 0 &&
        !replayJson
      ) {
        throw new Error("No query provided");
      }

      if (variables.q) dispatch(setInitialPrompt(variables.q));

      return OpenHands.createConversation(
        selectedRepository || undefined,
        variables.q,
        files,
        replayJson || undefined,
      );
    },
    onSuccess: async (data, { q }) => {
      if (!data) return;
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
      data.conversation_id &&
        navigate(`/conversations/${data.conversation_id}`);
    },
  });
};
