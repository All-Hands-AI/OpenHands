import { useState, useEffect } from "react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import { AgentState } from "#/types/agent-state";

// Initial agent state
const initialAgentState = AgentState.LOADING;

/**
 * Hook to access and manipulate agent state
 * This replaces the Redux agent slice functionality without using React Query
 */
export function useAgentState() {
  const [agentState, setAgentState] = useState<AgentState>(initialAgentState);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from Redux on mount
  useEffect(() => {
    try {
      const bridge = getQueryReduxBridge();
      const reduxState = bridge.getReduxSliceState<{
        curAgentState: AgentState;
      }>("agent");
      setAgentState(reduxState.curAgentState);
    } catch (error) {
      // If we can't get the state from Redux, use the initial state
      // eslint-disable-next-line no-console
      console.warn("Could not get agent state from Redux, using default");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Function to update agent state
  const setCurrentAgentState = (newState: AgentState) => {
    setAgentState(newState);
  };

  return {
    curAgentState: agentState,
    isLoading,
    setCurrentAgentState,
  };
}
