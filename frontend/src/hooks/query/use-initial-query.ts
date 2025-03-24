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
 * Hook to access and manipulate initial query data
 * This replaces the Redux initialQuery slice functionality without using React Query
 */
export function useInitialQuery() {
  const [state, setState] = useState<InitialQueryState>(initialState);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from Redux on mount
  useEffect(() => {
    try {
      const bridge = getQueryReduxBridge();
      const reduxState =
        bridge.getReduxSliceState<InitialQueryState>("initialQuery");
      setState(reduxState);
    } catch (error) {
      // If we can't get the state from Redux, use the initial state
      // eslint-disable-next-line no-console
      console.warn(
        "Could not get initial query state from Redux, using default",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // File operations
  const addFile = (file: string) => {
    setState((prev) => ({
      ...prev,
      files: [...prev.files, file],
    }));
  };

  const removeFile = (index: number) => {
    setState((prev) => {
      const newFiles = [...prev.files];
      newFiles.splice(index, 1);
      return {
        ...prev,
        files: newFiles,
      };
    });
  };

  const clearFiles = () => {
    setState((prev) => ({
      ...prev,
      files: [],
    }));
  };

  // Initial prompt operations
  const setInitialPrompt = (prompt: string) => {
    setState((prev) => ({
      ...prev,
      initialPrompt: prompt,
    }));
  };

  const clearInitialPrompt = () => {
    setState((prev) => ({
      ...prev,
      initialPrompt: null,
    }));
  };

  // Repository operations
  const setSelectedRepository = (repository: string | null) => {
    setState((prev) => ({
      ...prev,
      selectedRepository: repository,
    }));
  };

  const clearSelectedRepository = () => {
    setState((prev) => ({
      ...prev,
      selectedRepository: null,
    }));
  };

  return {
    // State
    files: state?.files || initialState.files,
    initialPrompt: state?.initialPrompt || initialState.initialPrompt,
    selectedRepository:
      state?.selectedRepository || initialState.selectedRepository,
    isLoading,

    // Actions
    addFile,
    removeFile,
    clearFiles,
    setInitialPrompt,
    clearInitialPrompt,
    setSelectedRepository,
    clearSelectedRepository,
  };
}
