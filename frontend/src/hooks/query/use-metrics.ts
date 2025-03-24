import { useQuery, useQueryClient } from "@tanstack/react-query";

interface MetricsState {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

// Initial metrics state
const initialMetrics: MetricsState = {
  cost: null,
  usage: null,
};

// Query key for metrics
export const METRICS_QUERY_KEY = ["metrics"];

/**
 * Helper function to set metrics
 */
export function setMetrics(
  queryClient: ReturnType<typeof useQueryClient>,
  metrics: MetricsState,
) {
  queryClient.setQueryData(METRICS_QUERY_KEY, metrics);
}

/**
 * Hook to access and manipulate metrics data using React Query
 * This provides the metrics slice functionality
 */
export function useMetrics() {
  const queryClient = useQueryClient();

  // Query for metrics
  const query = useQuery({
    queryKey: METRICS_QUERY_KEY,
    queryFn: () => {
      // If we already have data in React Query, use that
      const existingData =
        queryClient.getQueryData<MetricsState>(METRICS_QUERY_KEY);
      if (existingData) return existingData;

      // If no existing data, return the initial state
      return initialMetrics;
    },
    initialData: initialMetrics,
    staleTime: Infinity, // We manage updates manually
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Create a setter function that components can use
  const setMetricsState = (newMetrics: MetricsState) => {
    setMetrics(queryClient, newMetrics);
  };

  return {
    metrics: query.data || initialMetrics,
    isLoading: query.isLoading,
    setMetrics: setMetricsState,
  };
}
