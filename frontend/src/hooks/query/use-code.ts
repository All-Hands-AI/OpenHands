import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

export interface FileState {
  path: string;
  savedContent: string;
  unsavedContent: string;
}

interface CodeState {
  code: string;
  path: string;
  refreshID: number;
  fileStates: FileState[];
}

// Initial state
const initialCode: CodeState = {
  code: "",
  path: "",
  refreshID: 0,
  fileStates: [],
};

/**
 * Hook to access and manipulate code data using React Query
 * This replaces the Redux code slice functionality
 */
export function useCode() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    // eslint-disable-next-line no-console
    console.warn("QueryReduxBridge not initialized, using default code state");
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialCodeState = (): CodeState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<CodeState>(["code"]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<CodeState>("code");
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialCode;
      }
    }

    // If bridge is not available, return the initial state
    return initialCode;
  };

  // Query for code state
  const query = useQuery({
    queryKey: ["code"],
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<CodeState>(["code"]);
      if (existingData) return existingData;

      // Otherwise get from the bridge or use initial state
      return getInitialCodeState();
    },
    initialData: initialCode, // Use initialCode directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Function to set code (synchronous)
  const setCode = (code: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CodeState>(["code"]) || initialCode;

    // Update state
    const newState = {
      ...previousState,
      code,
    };

    // Set the state synchronously
    queryClient.setQueryData<CodeState>(["code"], newState);
  };

  // Function to set active filepath (synchronous)
  const setActiveFilepath = (path: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CodeState>(["code"]) || initialCode;

    // Update state
    const newState = {
      ...previousState,
      path,
    };

    // Set the state synchronously
    queryClient.setQueryData<CodeState>(["code"], newState);
  };

  // Function to set refresh ID (synchronous)
  const setRefreshID = (refreshID: number) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CodeState>(["code"]) || initialCode;

    // Update state
    const newState = {
      ...previousState,
      refreshID,
    };

    // Set the state synchronously
    queryClient.setQueryData<CodeState>(["code"], newState);
  };

  // Function to set file states (synchronous)
  const setFileStates = (fileStates: FileState[]) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CodeState>(["code"]) || initialCode;

    // Update state
    const newState = {
      ...previousState,
      fileStates,
    };

    // Set the state synchronously
    queryClient.setQueryData<CodeState>(["code"], newState);
  };

  // Function to add or update file state (synchronous)
  const addOrUpdateFileState = (fileState: FileState) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CodeState>(["code"]) || initialCode;

    // Filter out the file state with the same path
    const newFileStates = previousState.fileStates.filter(
      (fs) => fs.path !== fileState.path,
    );

    // Add the new file state
    newFileStates.push(fileState);

    // Update state
    const newState = {
      ...previousState,
      fileStates: newFileStates,
    };

    // Set the state synchronously
    queryClient.setQueryData<CodeState>(["code"], newState);
  };

  // Function to remove file state (synchronous)
  const removeFileState = (path: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CodeState>(["code"]) || initialCode;

    // Filter out the file state with the given path
    const newFileStates = previousState.fileStates.filter(
      (fs) => fs.path !== path,
    );

    // Update state
    const newState = {
      ...previousState,
      fileStates: newFileStates,
    };

    // Set the state synchronously
    queryClient.setQueryData<CodeState>(["code"], newState);
  };

  return {
    // State
    code: query.data?.code || initialCode.code,
    path: query.data?.path || initialCode.path,
    refreshID: query.data?.refreshID || initialCode.refreshID,
    fileStates: query.data?.fileStates || initialCode.fileStates,
    isLoading: query.isLoading,

    // Actions
    setCode,
    setActiveFilepath,
    setRefreshID,
    setFileStates,
    addOrUpdateFileState,
    removeFileState,
  };
}
