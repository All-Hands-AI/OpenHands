import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AgentState } from "#/types/agent-state";

interface AgentStateData {
  curAgentState: AgentState;
}

// Initial agent state
const initialAgentState: AgentStateData = {
  curAgentState: AgentState.LOADING,
};

// Query key for agent state
export const AGENT_STATE_QUERY_KEY = ["agent"];

/**
 * Helper function to set agent state
 */
export function setAgentState(
  queryClient: ReturnType<typeof useQueryClient>,
  agentState: AgentState,
) {
  queryClient.setQueryData(AGENT_STATE_QUERY_KEY, {
    curAgentState: agentState,
  });
}

/**
 * Hook to access and manipulate agent state using React Query
 * This provides the agent slice functionality
 */
export function useAgentState() {
  const queryClient = useQueryClient();

  // Query for agent state
  const query = useQuery({
    queryKey: AGENT_STATE_QUERY_KEY,
    queryFn: () => {
      // If we already have data in React Query, use that
      const existingData = queryClient.getQueryData<AgentStateData>(
        AGENT_STATE_QUERY_KEY,
      );
      if (existingData) return existingData;

      // If no existing data, return the initial state
      return initialAgentState;
    },
    initialData: initialAgentState,
    staleTime: Infinity, // We manage updates manually
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Create a setter function that components can use
  const setCurrentAgentState = (newAgentState: AgentState) => {
    setAgentState(queryClient, newAgentState);
  };

  return {
    curAgentState: query.data?.curAgentState || initialAgentState.curAgentState,
    isLoading: query.isLoading,
    setCurrentAgentState,
  };
}
