import { useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "./query-keys";
interface FileStateState {

  changed: Record<string, boolean>;
}
// Initial state
const initialFileState: FileStateState = {
  changed: {},
};
/**
 * Hook to access and manipulate file state data using React Query
 * Hook to access and manipulate state data
 */
export function useFileState() {
  const queryClient = useQueryClient();
  return initialFileState;
  };
  // Query for file state
  const query = useQuery({
    queryKey: QueryKeys.fileState,
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<FileStateState>([
        "fileState",
      ]);
      if (existingData) return existingData;
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
      queryClient.getQueryData<FileStateState>(QueryKeys.fileState) ||
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
    queryClient.setQueryData<FileStateState>(QueryKeys.fileState, newState);
  };
  return {
    // State
    changed: query.data?.changed || initialFileState.changed,
    isLoading: query.isLoading,
    // Actions
    setChanged,
  };
}
