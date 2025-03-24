import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AgentState } from "#/types/agent-state";

interface AgentStateData {
  curAgentState: AgentState;
}

// Initial agent state
const initialAgentState: AgentStateData = {
  curAgentState: AgentState.LOADING,
};

/**
 * Hook to access and manipulate agent state using React Query
 * This provides the agent slice functionality
 */
export function useAgentState() {
  const queryClient = useQueryClient();

  // Get initial state from cache if this is the first time accessing the data
  const getInitialAgentState = (): AgentStateData => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<AgentStateData>(["agent"]);
    if (existingData) return existingData;

    // If no existing data, return the initial state
    return initialAgentState;
  };

  // Query for agent state
  const query = useQuery({
    queryKey: ["agent"],
    queryFn: () => getInitialAgentState(),
    initialData: initialAgentState,
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Mutation to set agent state
  const setAgentStateMutation = useMutation({
    mutationFn: (agentState: AgentState) =>
      Promise.resolve({ curAgentState: agentState }),
    onMutate: async (agentState) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["agent"],
      });

      // Get current agent state
      const previousAgentState = queryClient.getQueryData<AgentStateData>([
        "agent",
      ]);

      // Update agent state
      queryClient.setQueryData(["agent"], { curAgentState: agentState });

      return { previousAgentState };
    },
    onError: (_, __, context) => {
      // Restore previous agent state on error
      if (context?.previousAgentState) {
        queryClient.setQueryData(["agent"], context.previousAgentState);
      }
    },
  });

  return {
    curAgentState: query.data?.curAgentState || initialAgentState.curAgentState,
    isLoading: query.isLoading,
    setCurrentAgentState: setAgentStateMutation.mutate,
  };
}
