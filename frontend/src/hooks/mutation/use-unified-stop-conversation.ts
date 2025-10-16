import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import toast from "react-hot-toast";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";
import {
  getConversationVersionFromQueryCache,
  stopV1Conversation,
  stopV0Conversation,
  updateConversationStatusInCache,
  invalidateConversationQueries,
} from "./conversation-mutation-utils";

/**
 * Unified hook that automatically routes to the correct stop conversation implementation
 * based on the conversation version (V0 or V1).
 *
 * This hook checks the cached conversation data to determine the version, then calls
 * the appropriate API directly. Returns a single useMutation instance that all components share.
 *
 * Usage is the same as useStopConversation:
 * const { mutate: stopConversation } = useUnifiedStopConversation();
 * stopConversation({ conversationId: "some-id" });
 */
export const useUnifiedStopConversation = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const params = useParams<{ conversationId: string }>();

  return useMutation({
    mutationKey: ["stop-conversation"],
    mutationFn: async (variables: {
      conversationId: string;
      version?: "V0" | "V1";
    }) => {
      // Use provided version or fallback to cache lookup
      const version =
        variables.version ||
        getConversationVersionFromQueryCache(
          queryClient,
          variables.conversationId,
        );

      if (version === "V1") {
        return stopV1Conversation(variables.conversationId);
      }

      return stopV0Conversation(variables.conversationId);
    },
    onMutate: async () => {
      toast.loading("Stopping conversation...", TOAST_OPTIONS);

      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      return { previousConversations };
    },
    onError: (_, __, context) => {
      toast.dismiss();
      toast.error("Failed to stop conversation", TOAST_OPTIONS);

      if (context?.previousConversations) {
        queryClient.setQueryData(
          ["user", "conversations"],
          context.previousConversations,
        );
      }
    },
    onSettled: (_, __, variables) => {
      invalidateConversationQueries(queryClient, variables.conversationId);
    },
    onSuccess: (_, variables) => {
      toast.dismiss();
      toast.success("Conversation stopped", TOAST_OPTIONS);

      updateConversationStatusInCache(
        queryClient,
        variables.conversationId,
        "STOPPED",
      );

      // Only redirect if we're stopping the conversation we're currently viewing
      if (params.conversationId === variables.conversationId) {
        navigate("/");
      }
    },
  });
};
