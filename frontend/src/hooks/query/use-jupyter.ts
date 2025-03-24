import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQueryClientWrapper } from "#/utils/query-client-wrapper";

export type Cell = {
  content: string;
  type: "input" | "output";
};

interface JupyterState {
  cells: Cell[];
}

// Initial state
const initialJupyter: JupyterState = {
  cells: [],
};

/**
 * Hook to access and manipulate jupyter data using React Query
 * This provides the jupyter slice functionality
 */
export function useJupyter() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryClientWrapper> | null = null;
  try {
    bridge = getQueryClientWrapper();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    // eslint-disable-next-line no-console
    console.warn(
      "QueryReduxBridge not initialized, using default jupyter state",
    );
  }

  // Get initial state from cache if this is the first time accessing the data
  const getInitialJupyterState = (): JupyterState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<JupyterState>(["jupyter"]);
    if (existingData) return existingData;

    // Otherwise, get initial data from cache if bridge is available
    if (bridge) {
      try {
        return bridge.getSliceState<JupyterState>("jupyter");
      } catch (error) {
        // If we can.t get the state from cache, return the initial state
        return initialJupyter;
      }
    }

    // If bridge is not available, return the initial state
    return initialJupyter;
  };

  // Query for jupyter state
  const query = useQuery({
    queryKey: ["jupyter"],
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<JupyterState>(["jupyter"]);
      if (existingData) return existingData;

      // Otherwise get from the bridge or use initial state
      return getInitialJupyterState();
    },
    initialData: initialJupyter, // Use initialJupyter directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Function to append jupyter input (synchronous)
  const appendJupyterInput = (content: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<JupyterState>(["jupyter"]) || initialJupyter;

    // Update state
    const newState = {
      ...previousState,
      cells: [...previousState.cells, { content, type: "input" as const }],
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Jupyter Debug] Appending input:", {
      content,
      cellsLength: newState.cells.length,
    });

    // Set the state synchronously
    queryClient.setQueryData<JupyterState>(["jupyter"], newState);
  };

  // Function to append jupyter output (synchronous)
  const appendJupyterOutput = (content: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<JupyterState>(["jupyter"]) || initialJupyter;

    // Update state
    const newState = {
      ...previousState,
      cells: [...previousState.cells, { content, type: "output" as const }],
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Jupyter Debug] Appending output:", {
      contentLength: content.length,
      cellsLength: newState.cells.length,
    });

    // Set the state synchronously
    queryClient.setQueryData<JupyterState>(["jupyter"], newState);
  };

  // Function to clear jupyter (synchronous)
  const clearJupyter = () => {
    // Update state
    const newState = {
      cells: [],
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Jupyter Debug] Clearing jupyter");

    // Set the state synchronously
    queryClient.setQueryData<JupyterState>(["jupyter"], newState);
  };

  return {
    // State
    cells: query.data?.cells || initialJupyter.cells,
    isLoading: query.isLoading,

    // Actions
    appendJupyterInput,
    appendJupyterOutput,
    clearJupyter,
  };
}
