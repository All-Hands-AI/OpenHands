import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
 * Hook to access and manipulate initial query data using React Query
 * This replaces the Redux initialQuery slice functionality
 */
export function useInitialQuery() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    console.warn(
      "QueryReduxBridge not initialized, using default initial query state",
    );
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialQueryState = (): InitialQueryState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<InitialQueryState>([
      "initialQuery",
    ]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<InitialQueryState>("initialQuery");
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialState;
      }
    }

    // If bridge is not available, return the initial state
    return initialState;
  };

  // Query for initial query state
  const query = useQuery({
    queryKey: ["initialQuery"],
    queryFn: () => getInitialQueryState(),
    initialData: initialState, // Use initialState directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Mutation to add a file
  const addFileMutation = useMutation({
    mutationFn: (file: string) => Promise.resolve(file),
    onMutate: async (file) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          files: [...previousState.files, file],
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  // Mutation to remove a file
  const removeFileMutation = useMutation({
    mutationFn: (index: number) => Promise.resolve(index),
    onMutate: async (index) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        const newFiles = [...previousState.files];
        newFiles.splice(index, 1);
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          files: newFiles,
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  // Mutation to clear files
  const clearFilesMutation = useMutation({
    mutationFn: () => Promise.resolve(),
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          files: [],
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  // Mutation to set initial prompt
  const setInitialPromptMutation = useMutation({
    mutationFn: (prompt: string) => Promise.resolve(prompt),
    onMutate: async (prompt) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          initialPrompt: prompt,
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  // Mutation to clear initial prompt
  const clearInitialPromptMutation = useMutation({
    mutationFn: () => Promise.resolve(),
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          initialPrompt: null,
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  // Mutation to set selected repository
  const setSelectedRepositoryMutation = useMutation({
    mutationFn: (repository: string | null) => Promise.resolve(repository),
    onMutate: async (repository) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          selectedRepository: repository,
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  // Mutation to clear selected repository
  const clearSelectedRepositoryMutation = useMutation({
    mutationFn: () => Promise.resolve(),
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["initialQuery"] });

      // Get current state
      const previousState = queryClient.getQueryData<InitialQueryState>([
        "initialQuery",
      ]);

      // Update state
      if (previousState) {
        queryClient.setQueryData<InitialQueryState>(["initialQuery"], {
          ...previousState,
          selectedRepository: null,
        });
      }

      return { previousState };
    },
    onError: (_, __, context) => {
      // Restore previous state on error
      if (context?.previousState) {
        queryClient.setQueryData(["initialQuery"], context.previousState);
      }
    },
  });

  return {
    // State
    files: query.data?.files || initialState.files,
    initialPrompt: query.data?.initialPrompt || initialState.initialPrompt,
    selectedRepository:
      query.data?.selectedRepository || initialState.selectedRepository,
    isLoading: query.isLoading,

    // Actions
    addFile: addFileMutation.mutate,
    removeFile: removeFileMutation.mutate,
    clearFiles: clearFilesMutation.mutate,
    setInitialPrompt: setInitialPromptMutation.mutate,
    clearInitialPrompt: clearInitialPromptMutation.mutate,
    setSelectedRepository: setSelectedRepositoryMutation.mutate,
    clearSelectedRepository: clearSelectedRepositoryMutation.mutate,
  };
}
