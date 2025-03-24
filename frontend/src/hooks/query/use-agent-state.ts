import { useQueryClient, useQuery } from "@tanstack/react-query";
import { AgentState } from "#/types/agent-state";

// Query key for agent state
const AGENT_STATE_QUERY_KEY = ["_STATE", "agent", "state"];

/**
 * Sets the agent state in the query cache
 * @param queryClient - The React Query client
 * @param state - The agent state to set
 */
export function setAgentState(
  queryClient: ReturnType<typeof useQueryClient>,
  state: AgentState,
) {
  queryClient.setQueryData(AGENT_STATE_QUERY_KEY, state);
}

/**
 * Hook to access and manage agent state
 * @returns Object containing the current agent state and a setter function
 */
export function useAgentState(): {
  agentState: AgentState;
  setAgentState: (state: AgentState) => void;
} {
  const queryClient = useQueryClient();

  // Get the current agent state from the query cache with a default of LOADING
  const { data: agentState = AgentState.LOADING } = useQuery({
    queryKey: AGENT_STATE_QUERY_KEY,
    // This is a placeholder query function that will never be called
    // since we're manually setting the data with setAgentState
    queryFn: () => Promise.resolve(AgentState.LOADING),
    // Don't refetch this data automatically
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    staleTime: Infinity,
  });

  // Create a setter function that components can use
  const setAgentStateFn = (newState: AgentState) => {
    setAgentState(queryClient, newState);
  };

  return {
    agentState,
    setAgentState: setAgentStateFn,
  };
}