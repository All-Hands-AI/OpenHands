import { useQuery } from "@tanstack/react-query";
import { useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "../use-conversation-id";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";

export const useConversationMicroagents = () => {
  const { conversationId } = useConversationId();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  return useQuery({
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
      curAgentState !== AgentState.LOADING &&
      curAgentState !== AgentState.INIT,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
