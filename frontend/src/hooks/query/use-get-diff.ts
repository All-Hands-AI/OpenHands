import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { GitChangeStatus } from "#/api/open-hands.types";
import { useConversation } from "#/context/conversation-context";

type UseGetDiffConfig = {
  filePath: string;
  type: GitChangeStatus;
  enabled: boolean;
};

export const useGitDiff = (config: UseGetDiffConfig) => {
  const { conversationId } = useConversation();

  return useQuery({
    queryKey: ["file_diff", conversationId, config.filePath, config.type],
    queryFn: () => OpenHands.getGitChangeDiff(conversationId, config.filePath),
    enabled: config.enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
