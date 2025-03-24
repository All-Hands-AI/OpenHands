import { useState, useEffect } from "react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

interface InitialQueryState {
  files: string[]; // base64 encoded images
  initialPrompt: string | null;
  selectedRepository: string | null;
}

// Initial state
const initialState: InitialQueryState = {
  files: [],
  initialPrompt: null,
  selectedRepository: null,
};

/**
 * Simplified hook to access and manipulate initial query data
 * This replaces the Redux initialQuery slice functionality without using React Query
 */
export function useInitialQuery() {
  const [state, setState] = useState<InitialQueryState>(initialState);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from Redux on mount
  useEffect(() => {
    try {
      const bridge = getQueryReduxBridge();
      const reduxState = bridge.getReduxSliceState<InitialQueryState>("initialQuery");
      setState(reduxState);
    } catch (error) {
      // If we can't get the state from Redux, use the initial state
      console.warn("Could not get initial query state from Redux, using default");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Functions to update state
  const setFiles = (files: string[]) => {
    setState((prev) => ({ ...prev, files }));
  };

  const setInitialPrompt = (initialPrompt: string | null) => {
    setState((prev) => ({ ...prev, initialPrompt }));
  };

  const setSelectedRepository = (selectedRepository: string | null) => {
    setState((prev) => ({ ...prev, selectedRepository }));
  };

  const resetState = () => {
    setState(initialState);
  };

  return {
    files: state.files,
    initialPrompt: state.initialPrompt,
    selectedRepository: state.selectedRepository,
    isLoading,
    setFiles,
    setInitialPrompt,
    setSelectedRepository,
    resetState,
  };
}