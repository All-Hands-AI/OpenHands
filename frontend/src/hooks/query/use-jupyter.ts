import { useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "./query-keys";

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
 * Hook to access and manipulate state data
 */
export function useJupyter() {
  const queryClient = useQueryClient();
  const getInitialJupyterState = (): JupyterState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<JupyterState>(
      QueryKeys.jupyter,
    );
    if (existingData) return existingData;
    return initialJupyter;
    return initialJupyter;
  };
  // Query for jupyter state
  const query = useQuery({
    queryKey: QueryKeys.jupyter,
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<JupyterState>(
        QueryKeys.jupyter,
      );
      if (existingData) return existingData;
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
      queryClient.getQueryData<JupyterState>(QueryKeys.jupyter) ||
      initialJupyter;
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
    queryClient.setQueryData<JupyterState>(QueryKeys.jupyter, newState);
  };
  // Function to append jupyter output (synchronous)
  const appendJupyterOutput = (content: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<JupyterState>(QueryKeys.jupyter) ||
      initialJupyter;
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
    queryClient.setQueryData<JupyterState>(QueryKeys.jupyter, newState);
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
    queryClient.setQueryData<JupyterState>(QueryKeys.jupyter, newState);
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
