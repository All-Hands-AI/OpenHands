import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
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
 * This replaces the Redux agent slice functionality
 */
export function useAgentState() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    console.warn("QueryReduxBridge not initialized, using default agent state");
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialAgentState = (): AgentStateData => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<AgentStateData>(["agent"]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<AgentStateData>("agent");
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialAgentState;
      }
    }

    // If bridge is not available, return the initial state
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
