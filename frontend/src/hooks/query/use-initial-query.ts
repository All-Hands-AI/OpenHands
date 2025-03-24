import { useQuery, useQueryClient } from "@tanstack/react-query";

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

// Query key for initial query
export const INITIAL_QUERY_KEY = ["initialQuery"];

/**
 * Helper functions to update initial query state
 */
export function updateInitialQueryState(
  queryClient: ReturnType<typeof useQueryClient>,
  updater: (state: InitialQueryState) => InitialQueryState,
) {
  const currentState =
    queryClient.getQueryData<InitialQueryState>(INITIAL_QUERY_KEY) ||
    initialState;
  const newState = updater(currentState);
  queryClient.setQueryData(INITIAL_QUERY_KEY, newState);
}

/**
 * Hook to access and manipulate initial query data using React Query
 * This provides the initialQuery slice functionality
 */
export function useInitialQuery() {
  const queryClient = useQueryClient();

  // Query for initial query state
  const query = useQuery({
    queryKey: INITIAL_QUERY_KEY,
    queryFn: () => {
      // If we already have data in React Query, use that
      const existingData =
        queryClient.getQueryData<InitialQueryState>(INITIAL_QUERY_KEY);
      if (existingData) return existingData;

      // If no existing data, return the initial state
      return initialState;
    },
    initialData: initialState,
    staleTime: Infinity, // We manage updates manually
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Create setter functions that components can use
  const addFile = (file: string) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      files: [...state.files, file],
    }));
  };

  const removeFile = (index: number) => {
    updateInitialQueryState(queryClient, (state) => {
      const newFiles = [...state.files];
      newFiles.splice(index, 1);
      return {
        ...state,
        files: newFiles,
      };
    });
  };

  const clearFiles = () => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      files: [],
    }));
  };

  const setInitialPrompt = (prompt: string) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      initialPrompt: prompt,
    }));
  };

  const clearInitialPrompt = () => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      initialPrompt: null,
    }));
  };

  const setSelectedRepository = (repository: string | null) => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      selectedRepository: repository,
    }));
  };

  const clearSelectedRepository = () => {
    updateInitialQueryState(queryClient, (state) => ({
      ...state,
      selectedRepository: null,
    }));
  };

  return {
    // State
    files: query.data?.files || initialState.files,
    initialPrompt: query.data?.initialPrompt || initialState.initialPrompt,
    selectedRepository:
      query.data?.selectedRepository || initialState.selectedRepository,
    isLoading: query.isLoading,

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
