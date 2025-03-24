import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

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

/**
 * Hook to access and manipulate metrics data using React Query
 * This provides the metrics slice functionality
 */
export function useMetrics() {
  const queryClient = useQueryClient();

  // Get initial state from cache if this is the first time accessing the data
  const getInitialMetricsState = (): MetricsState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<MetricsState>(["metrics"]);
    if (existingData) return existingData;

    // If no existing data, return the initial state
    return initialMetrics;
  };

  // Query for metrics
  const query = useQuery({
    queryKey: ["metrics"],
    queryFn: () => getInitialMetricsState(),
    initialData: initialMetrics, // Use initialMetrics directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Mutation to set metrics
  const setMetricsMutation = useMutation({
    mutationFn: (metrics: MetricsState) => Promise.resolve(metrics),
    onMutate: async (metrics) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["metrics"],
      });

      // Get current metrics
      const previousMetrics = queryClient.getQueryData<MetricsState>([
        "metrics",
      ]);

      // Update metrics
      queryClient.setQueryData(["metrics"], metrics);

      return { previousMetrics };
    },
    onError: (_, __, context) => {
      // Restore previous metrics on error
      if (context?.previousMetrics) {
        queryClient.setQueryData(["metrics"], context.previousMetrics);
      }
    },
  });

  return {
    metrics: query.data || initialMetrics,
    isLoading: query.isLoading,
    setMetrics: setMetricsMutation.mutate,
  };
}
