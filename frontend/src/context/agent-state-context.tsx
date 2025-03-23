import React, { createContext, useContext, ReactNode, useEffect } from "react";
import { useAgentState } from "#/hooks/state/use-agent-state";
import { AgentState } from "#/types/agent-state";
import { registerAgentStateService } from "#/services/context-services/agent-state-service";

interface AgentStateContextType {
  curAgentState: AgentState;
  updateAgentState: (state: AgentState) => void;
  resetAgentState: () => void;
}

const AgentStateContext = createContext<AgentStateContextType | undefined>(
  undefined,
);

/**
 * Provider component for agent state
 */
export function AgentStateProvider({ children }: { children: ReactNode }) {
  const agentState = useAgentState();

  // Register the update function with the service
  useEffect(() => {
    registerAgentStateService(agentState.updateAgentState);
  }, [agentState.updateAgentState]);

  return (
    <AgentStateContext.Provider value={agentState}>
      {children}
    </AgentStateContext.Provider>
  );
}

/**
 * Hook to use the agent state context
 */
export function useAgentStateContext() {
  const context = useContext(AgentStateContext);

  if (context === undefined) {
    throw new Error(
      "useAgentStateContext must be used within an AgentStateProvider",
    );
  }

  return context;
}
