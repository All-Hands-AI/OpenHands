import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import { AgentState } from "#/types/agent-state";

interface AgentStateState {
  curAgentState: AgentState;
}

// Initial state
const initialAgentState: AgentStateState = {
  curAgentState: AgentState.LOADING,
};

/**
 * Hook to access and manipulate agent state data using React Query
 * This replaces the Redux agent slice functionality
 */
export function useAgent() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    // eslint-disable-next-line no-console
    console.warn("QueryReduxBridge not initialized, using default agent state");
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialAgentState = (): AgentStateState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<AgentStateState>(["agent"]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<AgentStateState>("agent");
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
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<AgentStateState>(["agent"]);
      if (existingData) return existingData;

      // Otherwise get from the bridge or use initial state
      return getInitialAgentState();
    },
    initialData: initialAgentState, // Use initialAgentState directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Function to set current agent state (synchronous)
  const setCurrentAgentState = (curAgentState: AgentState) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<AgentStateState>(["agent"]) || initialAgentState;

    // Update state
    const newState = {
      ...previousState,
      curAgentState,
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Agent Debug] Setting agent state:", {
      previousState: previousState.curAgentState,
      newState: curAgentState,
    });

    // Set the state synchronously
    queryClient.setQueryData<AgentStateState>(["agent"], newState);
  };

  return {
    // State
    curAgentState: query.data?.curAgentState || initialAgentState.curAgentState,
    isLoading: query.isLoading,

    // Actions
    setCurrentAgentState,
  };
}
