import { AgentState } from "#/types/agent-state";

// Global reference to the agent state update function
// This will be set by the AgentStateProvider when it mounts
let updateAgentStateFn: ((state: AgentState) => void) | null = null;

/**
 * Register the agent state update function
 * This should be called by the AgentStateProvider when it mounts
 */
export function registerAgentStateService(
  updateFn: (state: AgentState) => void,
) {
  updateAgentStateFn = updateFn;
}

/**
 * Update the agent state
 * This is used by the actions service
 */
export function updateAgentState(state: AgentState) {
  // If the context provider is registered, use it
  if (updateAgentStateFn) {
    updateAgentStateFn(state);
  }

  // Redux store has been removed in the React Query migration
}
