import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation";

export function useGitDiff(filePath: string | null) {
  const { conversationId } = useConversation();

  return useQuery(
    ["gitDiff", conversationId, filePath],
    () => OpenHands.getGitDiff(conversationId, filePath!),
    {
      enabled: !!conversationId && !!filePath,
      staleTime: 1000 * 60 * 5, // 5 minutes
    }
  );
}