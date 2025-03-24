import React, { createContext, useContext, useState, ReactNode } from "react";
import { AgentState } from "#/types/agent-state";
import { StatusMessage } from "#/types/message";

// Define the shape of our global state
interface AppState {
  // Agent state
  agentState: AgentState;
  
  // Metrics state
  metrics: {
    cost: number | null;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    } | null;
  };
  
  // Status message
  statusMessage: StatusMessage;
  
  // Initial query
  initialQuery: {
    files: string[];
    initialPrompt: string | null;
    selectedRepository: string | null;
  };
}

// Define the shape of our context
interface AppStateContextType {
  state: AppState;
  setAgentState: (state: AgentState) => void;
  setMetrics: (metrics: AppState["metrics"]) => void;
  setStatusMessage: (message: StatusMessage) => void;
  setInitialQueryFiles: (files: string[]) => void;
  setInitialPrompt: (prompt: string | null) => void;
  setSelectedRepository: (repo: string | null) => void;
  resetInitialQuery: () => void;
}

// Create initial state
const initialState: AppState = {
  agentState: AgentState.LOADING,
  metrics: {
    cost: null,
    usage: null,
  },
  statusMessage: {
    status_update: true,
    type: "info",
    id: "",
    message: "",
  },
  initialQuery: {
    files: [],
    initialPrompt: null,
    selectedRepository: null,
  },
};

// Create context
const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

// Create provider component
export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(initialState);

  // Agent state updater
  const setAgentState = (agentState: AgentState) => {
    setState((prev) => ({ ...prev, agentState }));
  };

  // Metrics updater
  const setMetrics = (metrics: AppState["metrics"]) => {
    setState((prev) => ({ ...prev, metrics }));
  };

  // Status message updater
  const setStatusMessage = (statusMessage: StatusMessage) => {
    setState((prev) => ({ ...prev, statusMessage }));
  };

  // Initial query updaters
  const setInitialQueryFiles = (files: string[]) => {
    setState((prev) => ({
      ...prev,
      initialQuery: { ...prev.initialQuery, files },
    }));
  };

  const setInitialPrompt = (initialPrompt: string | null) => {
    setState((prev) => ({
      ...prev,
      initialQuery: { ...prev.initialQuery, initialPrompt },
    }));
  };

  const setSelectedRepository = (selectedRepository: string | null) => {
    setState((prev) => ({
      ...prev,
      initialQuery: { ...prev.initialQuery, selectedRepository },
    }));
  };

  const resetInitialQuery = () => {
    setState((prev) => ({
      ...prev,
      initialQuery: initialState.initialQuery,
    }));
  };

  // Create context value
  const contextValue: AppStateContextType = {
    state,
    setAgentState,
    setMetrics,
    setStatusMessage,
    setInitialQueryFiles,
    setInitialPrompt,
    setSelectedRepository,
    resetInitialQuery,
  };

  return (
    <AppStateContext.Provider value={contextValue}>
      {children}
    </AppStateContext.Provider>
  );
}

// Create hook to use the context
export function useAppState() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error("useAppState must be used within an AppStateProvider");
  }
  return context;
}

// Create individual hooks that match the API of the original hooks
export function useAgentState() {
  const { state, setAgentState } = useAppState();
  return {
    curAgentState: state.agentState,
    isLoading: false,
    setCurrentAgentState: setAgentState,
  };
}

export function useMetrics() {
  const { state, setMetrics } = useAppState();
  return {
    metrics: state.metrics,
    isLoading: false,
    setMetrics,
  };
}

export function useStatusMessage() {
  const { state, setStatusMessage } = useAppState();
  return {
    statusMessage: state.statusMessage,
    isLoading: false,
    setStatusMessage,
  };
}

export function useInitialQuery() {
  const {
    state,
    setInitialQueryFiles,
    setInitialPrompt,
    setSelectedRepository,
    resetInitialQuery,
  } = useAppState();
  
  return {
    files: state.initialQuery.files,
    initialPrompt: state.initialQuery.initialPrompt,
    selectedRepository: state.initialQuery.selectedRepository,
    isLoading: false,
    setFiles: setInitialQueryFiles,
    setInitialPrompt,
    setSelectedRepository,
    resetState: resetInitialQuery,
  };
}