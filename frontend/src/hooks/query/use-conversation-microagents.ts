import { useQuery } from "@tanstack/react-query";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useConversationId } from "../use-conversation-id";
import { AgentState } from "#/types/agent-state";
import { useAgentState } from "#/hooks/use-agent-state";

export const useConversationMicroagents = () => {
  const { conversationId } = useConversationId();
  const { curAgentState } = useAgentState();

  return useQuery({
    queryKey: ["conversation", conversationId, "microagents"],
    queryFn: async () => {
      if (!conversationId) {
        throw new Error("No conversation ID provided");
      }
      const data = await ConversationService.getMicroagents(conversationId);
      return data.microagents;
    },
    enabled:
      !!conversationId &&
      curAgentState !== AgentState.LOADING &&
      curAgentState !== AgentState.INIT,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
