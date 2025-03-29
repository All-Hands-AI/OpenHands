import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AgentState } from "#/types/agent-state";

interface AgentStateData {
  curAgentState: AgentState;
}

const initialAgentState: AgentStateData = {
  curAgentState: AgentState.LOADING,
};

export const AGENT_STATE_QUERY_KEY = ["agent"];

export function setAgentState(
  queryClient: ReturnType<typeof useQueryClient>,
  agentState: AgentState,
) {
  queryClient.setQueryData(AGENT_STATE_QUERY_KEY, {
    curAgentState: agentState,
  });
}

export function useAgentState() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: AGENT_STATE_QUERY_KEY,
    queryFn: () => {
      const existingData = queryClient.getQueryData<AgentStateData>(
        AGENT_STATE_QUERY_KEY,
      );
      if (existingData) return existingData;
      return initialAgentState;
    },
    initialData: initialAgentState,
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const setCurrentAgentState = (newAgentState: AgentState) => {
    setAgentState(queryClient, newAgentState);
  };

  return {
    curAgentState: query.data?.curAgentState || initialAgentState.curAgentState,
    isLoading: query.isLoading,
    setCurrentAgentState,
  };
}
