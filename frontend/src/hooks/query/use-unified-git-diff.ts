import { useQuery } from "@tanstack/react-query";
import GitService from "#/api/git-service/git-service.api";
import V1GitService from "#/api/git-service/v1-git-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import type { GitChangeStatus } from "#/api/open-hands.types";

type UseUnifiedGitDiffConfig = {
  filePath: string;
  type: GitChangeStatus;
  enabled: boolean;
};

/**
 * Unified hook to get git diff for both legacy (V0) and V1 conversations
 * - V0: Uses the legacy GitService.getGitChangeDiff API endpoint
 * - V1: Uses the V1GitService.getGitChangeDiff API endpoint with runtime URL
 */
export const useUnifiedGitDiff = (config: UseUnifiedGitDiffConfig) => {
  const { conversationId } = useConversationId();
  const { data: conversation } = useActiveConversation();

  const isV1Conversation = conversation?.conversation_version === "V1";
  const conversationUrl = conversation?.url;
  const sessionApiKey = conversation?.session_api_key;

  return useQuery({
    queryKey: [
      "unified",
      "file_diff",
      conversationId,
      config.filePath,
      config.type,
      isV1Conversation,
      conversationUrl,
    ],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");

      // V1: Use the V1 API endpoint with runtime URL
      if (isV1Conversation) {
        return V1GitService.getGitChangeDiff(
          conversationUrl,
          sessionApiKey,
          config.filePath,
        );
      }

      // V0 (Legacy): Use the legacy API endpoint
      return GitService.getGitChangeDiff(conversationId, config.filePath);
    },
    enabled: config.enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
