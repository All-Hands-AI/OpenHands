import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import posthog from "posthog-js";
import { useDispatch, useSelector } from "react-redux";
import { setInitialPrompt } from "#/state/initial-query-slice";
import { RootState } from "#/store";
import { ConversationService } from "#/api/conversation-service/conversation-service.api";
import { GitRepository } from "#/types/git";

const conversationMutationFn = async (
  selectedRepository: string | GitRepository | undefined,
  initialUserMsg: string | undefined,
  imageUrls: string[],
  replayJson: string | undefined,
) => {
  const hasInitialData =
    selectedRepository || initialUserMsg || imageUrls.length > 0 || replayJson;
  if (!hasInitialData) throw new Error("No query provided");

  return ConversationService.createConversation(
    selectedRepository,
    initialUserMsg,
    imageUrls,
    replayJson,
  );
};

export const useCreateConversation = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { selectedRepository, files, replayJson } = useSelector(
    (state: RootState) => state.initialQuery,
  );

  const handleSuccess = async (conversationId: string, q?: string) => {
    if (q) dispatch(setInitialPrompt(q));
    posthog.capture("initial_query_submitted", {
      entry_point: "task_form",
      query_character_length: q?.length,
      has_repository: !!selectedRepository,
      has_files: files.length > 0,
      has_replay_json: !!replayJson,
    });

    await queryClient.invalidateQueries({
      queryKey: ["conversations"],
    });
    await navigate(`/conversations/${conversationId}`);
  };

  return useMutation({
    mutationKey: ["create-conversation"],
    mutationFn: async (variables: {
      q?: string;
      selectedRepository?: GitRepository | null;
    }) => {
      if (variables.q) dispatch(setInitialPrompt(variables.q));

      return conversationMutationFn(
        variables.selectedRepository || selectedRepository || undefined,
        variables.q,
        files,
        replayJson || undefined,
      ),
    onSuccess: async ({ conversation_id: conversationId }, { q }) => {
      await handleSuccess(conversationId, q);
    },
  });
};
