import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import { useDispatch, useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { setInitialPrompt } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { SuggestedTask } from "#/components/features/home/tasks/task.types";
import { Provider } from "#/types/settings";

interface CreateConversationVariables {
  query?: string;
  repository?: {
    name: string;
    gitProvider: Provider;
    branch: string;
  };
  suggestedTask?: SuggestedTask;
  conversationInstructions?: string;
}

export const useCreateConversation = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const queryClient = useQueryClient();

  const { selectedRepository, files, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  return useMutation({
    mutationKey: ["create-conversation"],
    mutationFn: async (variables: CreateConversationVariables) => {
      const { query, repository, suggestedTask, conversationInstructions } =
        variables;

      if (query) dispatch(setInitialPrompt(query));

      return OpenHands.createConversation(
        repository?.name,
        repository?.gitProvider,
        query,
        files,
        replayJson || undefined,
        suggestedTask,
        repository?.branch,
        conversationInstructions,
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
      // navigate(`/conversations/${conversationId}`);
    },
  });
};
