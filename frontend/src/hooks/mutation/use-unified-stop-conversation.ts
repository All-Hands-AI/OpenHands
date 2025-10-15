import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import toast from "react-hot-toast";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";
import { TOAST_OPTIONS } from "#/utils/custom-toast-handlers";

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
    mutationFn: async (variables: { conversationId: string }) => {
      // Check the cache for the conversation version
      const conversation = queryClient.getQueryData<{
        conversation_version?: string;
      } | null>(["user", "conversation", variables.conversationId]);

      // Route to the appropriate API based on version
      if (conversation?.conversation_version === "V1") {
        // V1: Fetch app conversation to get sandbox_id, then pause sandbox
        const conversations =
          await V1ConversationService.batchGetAppConversations([
            variables.conversationId,
          ]);

        const appConversation = conversations[0];
        if (!appConversation) {
          throw new Error(
            `V1 conversation not found: ${variables.conversationId}`,
          );
        }

        return V1ConversationService.pauseSandbox(appConversation.sandbox_id);
      }

      // V0: Use the regular stop conversation API
      return ConversationService.stopConversation(variables.conversationId);
    },
    onMutate: async () => {
      // Show loading toast immediately
      toast.loading("Stopping conversation...", TOAST_OPTIONS);

      await queryClient.cancelQueries({ queryKey: ["user", "conversations"] });
      const previousConversations = queryClient.getQueryData([
        "user",
        "conversations",
      ]);

      return { previousConversations };
    },
    onError: (_, __, context) => {
      // Dismiss loading toast and show error
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
      // Invalidate the specific conversation query to trigger automatic refetch
      queryClient.invalidateQueries({
        queryKey: ["user", "conversation", variables.conversationId],
      });
      // Also invalidate the conversations list for consistency
      queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
      // Invalidate V1 batch get queries
      queryClient.invalidateQueries({
        queryKey: ["v1-batch-get-app-conversations"],
      });
    },
    onSuccess: (_, variables) => {
      // Dismiss loading toast and show success
      toast.dismiss();
      toast.success("Conversation stopped", TOAST_OPTIONS);

      // Optimistically update the conversation in the list cache
      queryClient.setQueriesData<{
        pages: Array<{
          results: Array<{ conversation_id: string; status: string }>;
        }>;
      }>({ queryKey: ["user", "conversations"] }, (oldData) => {
        if (!oldData) return oldData;

        return {
          ...oldData,
          pages: oldData.pages.map((page) => ({
            ...page,
            results: page.results.map((conv) =>
              conv.conversation_id === variables.conversationId
                ? { ...conv, status: "STOPPED" }
                : conv,
            ),
          })),
        };
      });

      // Only redirect if we're stopping the conversation we're currently viewing
      if (params.conversationId === variables.conversationId) {
        navigate("/");
      }
    },
  });
};
