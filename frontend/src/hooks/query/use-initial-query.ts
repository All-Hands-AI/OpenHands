import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

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
 * This provides the initialQuery slice functionality
 */
export function useInitialQuery() {
  const queryClient = useQueryClient();

  // Get initial state from cache if this is the first time accessing the data
  const getInitialInitialQueryState = (): InitialQueryState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<InitialQueryState>([
      "initialQuery",
    ]);
    if (existingData) return existingData;

    // If no existing data, return the initial state
    return initialState;
  };

  // Query for initial query state
  const query = useQuery({
    queryKey: ["initialQuery"],
    queryFn: () => getInitialInitialQueryState(),
    initialData: initialState,
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

  // Function to directly set the selected repository (synchronous)
  const setSelectedRepositorySync = (repository: string | null) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<InitialQueryState>(["initialQuery"]) ||
      initialState;

    // Update state
    const newState = {
      ...previousState,
      selectedRepository: repository,
    };

    // Set the state synchronously
    queryClient.setQueryData<InitialQueryState>(["initialQuery"], newState);
  };

  // We don't need the mutation anymore since we're using the sync function directly

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

  // No need to log the state anymore

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
    setSelectedRepository: setSelectedRepositorySync, // Use the synchronous function directly
    clearSelectedRepository: clearSelectedRepositoryMutation.mutate,
  };
}
