import { QueryClient } from "@tanstack/react-query";
import { Provider } from "#/types/settings";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import V1ConversationService from "#/api/conversation-service/v1-conversation-service.api";

/**
 * Gets the conversation version from the cache
 */
export const getConversationVersionFromQueryCache = (
  queryClient: QueryClient,
  conversationId: string,
): "V0" | "V1" => {
  const conversation = queryClient.getQueryData<{
    conversation_version?: string;
  }>(["user", "conversation", conversationId]);

  return conversation?.conversation_version === "V1" ? "V1" : "V0";
};

/**
 * Fetches a V1 conversation's sandbox_id
 */
const fetchV1ConversationSandboxId = async (
  conversationId: string,
): Promise<string> => {
  const conversations = await V1ConversationService.batchGetAppConversations([
    conversationId,
  ]);

  const appConversation = conversations[0];
  if (!appConversation) {
    throw new Error(`V1 conversation not found: ${conversationId}`);
  }

  return appConversation.sandbox_id;
};

/**
 * Pause a V1 conversation sandbox by fetching the sandbox_id and pausing it
 */
export const pauseV1ConversationSandbox = async (conversationId: string) => {
  const sandboxId = await fetchV1ConversationSandboxId(conversationId);
  return V1ConversationService.pauseSandbox(sandboxId);
};

/**
 * Stops a V0 conversation using the legacy API
 */
export const stopV0Conversation = async (conversationId: string) =>
  ConversationService.stopConversation(conversationId);

/**
 * Resumes a V1 conversation sandbox by fetching the sandbox_id and resuming it
 */
export const resumeV1ConversationSandbox = async (conversationId: string) => {
  const sandboxId = await fetchV1ConversationSandboxId(conversationId);
  return V1ConversationService.resumeSandbox(sandboxId);
};

/**
 * Starts a V0 conversation using the legacy API
 */
export const startV0Conversation = async (
  conversationId: string,
  providers?: Provider[],
) => ConversationService.startConversation(conversationId, providers);

/**
 * Optimistically updates the conversation status in the cache
 */
export const updateConversationStatusInCache = (
  queryClient: QueryClient,
  conversationId: string,
  status: string,
): void => {
  // Update the individual conversation cache
  queryClient.setQueryData<{ status: string }>(
    ["user", "conversation", conversationId],
    (oldData) => {
      if (!oldData) return oldData;
      return { ...oldData, status };
    },
  );

  // Update the conversations list cache
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
          conv.conversation_id === conversationId ? { ...conv, status } : conv,
        ),
      })),
    };
  });
};

/**
 * Invalidates all queries related to conversation mutations (start/stop)
 */
export const invalidateConversationQueries = (
  queryClient: QueryClient,
  conversationId: string,
): void => {
  // Invalidate the specific conversation query to trigger automatic refetch
  queryClient.invalidateQueries({
    queryKey: ["user", "conversation", conversationId],
  });
  // Also invalidate the conversations list for consistency
  queryClient.invalidateQueries({ queryKey: ["user", "conversations"] });
  // Invalidate V1 batch get queries
  queryClient.invalidateQueries({
    queryKey: ["v1-batch-get-app-conversations"],
  });
};
