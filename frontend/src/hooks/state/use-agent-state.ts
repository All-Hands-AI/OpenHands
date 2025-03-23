import { useState, useCallback } from "react";
import { AgentState } from "#/types/agent-state";

/**
 * Custom hook for managing agent state
 * This replaces the Redux agent-slice
 */
export function useAgentState() {
  const [curAgentState, setCurAgentState] = useState<AgentState>(
    AgentState.LOADING,
  );

  /**
   * Set the current agent state
   */
  const updateAgentState = useCallback((state: AgentState) => {
    setCurAgentState(state);
  }, []);

  /**
   * Reset the agent state to loading
   */
  const resetAgentState = useCallback(() => {
    setCurAgentState(AgentState.LOADING);
  }, []);

  return {
    curAgentState,
    updateAgentState,
    resetAgentState,
  };
}
