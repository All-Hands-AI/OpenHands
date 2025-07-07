import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { AgentState } from "#/types/agent-state";

interface UseConversationMicroagentsOptions {
  agentState?: AgentState;
  conversationId: string | undefined;
  enabled?: boolean;
}

export const useConversationMicroagents = ({
  agentState,
  conversationId,
  enabled = true,
}: UseConversationMicroagentsOptions) =>
  useQuery({
    queryKey: ["conversation", conversationId, "microagents"],
    queryFn: async () => {
      if (!conversationId) {
        throw new Error("No conversation ID provided");
      }
      const data = await OpenHands.getMicroagents(conversationId);
      return data.microagents;
    },
    enabled:
      !!conversationId &&
      enabled &&
      agentState !== AgentState.LOADING &&
      agentState !== AgentState.INIT,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
