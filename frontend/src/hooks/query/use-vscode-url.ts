import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useConversationContext } from "#/context/conversation-context";

export const useVSCodeUrl = (config: { enabled: boolean }) => {
  const { conversationId } = useConversationContext();

  const data = useQuery({
    queryKey: ["vscode_url", conversationId],
    queryFn: () => {
      if (!conversationId) throw new Error("No conversation ID");
      return OpenHands.getVSCodeUrl(conversationId);
    },
    enabled: !!conversationId && config.enabled,
    refetchOnMount: true,
  });

  return data;
};
