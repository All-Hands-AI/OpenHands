import { useQuery } from "@tanstack/react-query";
import GitService from "#/api/git-service/git-service.api";
import { GitChangeStatus } from "#/api/open-hands.types";
import { useConversationId } from "#/hooks/use-conversation-id";

type UseGetDiffConfig = {
  filePath: string;
  type: GitChangeStatus;
  enabled: boolean;
};

export const useGitDiff = (config: UseGetDiffConfig) => {
  const { conversationId } = useConversationId();

  return useQuery({
    queryKey: ["file_diff", conversationId, config.filePath, config.type],
    queryFn: () => GitService.getGitChangeDiff(conversationId, config.filePath),
    enabled: config.enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
