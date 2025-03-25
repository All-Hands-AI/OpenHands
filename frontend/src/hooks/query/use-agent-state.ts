import { useQueryClient } from "@tanstack/react-query";
import { AgentState } from "#/types/agent-state";

export function useAgentState() {
  const queryClient = useQueryClient();
  return queryClient.getQueryData<AgentState>(["_STATE", "agent"]) ?? AgentState.LOADING;
}