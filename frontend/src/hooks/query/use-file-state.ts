import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

interface FileStateState {
  changed: Record<string, boolean>;
}

// Initial state
const initialFileState: FileStateState = {
  changed: {},
};

/**
 * Hook to access and manipulate file state data using React Query
 * This replaces the Redux fileState slice functionality
 */
export function useFileState() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    // eslint-disable-next-line no-console
    console.warn("QueryReduxBridge not initialized, using default file state");
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialFileStateState = (): FileStateState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<FileStateState>([
      "fileState",
    ]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<FileStateState>("fileState");
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialFileState;
      }
    }

    // If bridge is not available, return the initial state
    return initialFileState;
  };

  // Query for file state
  const query = useQuery({
    queryKey: ["fileState"],
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<FileStateState>([
        "fileState",
      ]);
      if (existingData) return existingData;

      // Otherwise get from the bridge or use initial state
      return getInitialFileStateState();
    },
    initialData: initialFileState, // Use initialFileState directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Function to set changed state for a file path (synchronous)
  const setChanged = (path: string, changed: boolean) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<FileStateState>(["fileState"]) ||
      initialFileState;

    // Update state
    const newState = {
      ...previousState,
      changed: {
        ...previousState.changed,
        [path]: changed,
      },
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[FileState Debug] Setting changed state:", {
      path,
      changed,
      newState,
    });

    // Set the state synchronously
    queryClient.setQueryData<FileStateState>(["fileState"], newState);
  };

  return {
    // State
    changed: query.data?.changed || initialFileState.changed,
    isLoading: query.isLoading,

    // Actions
    setChanged,
  };
}
