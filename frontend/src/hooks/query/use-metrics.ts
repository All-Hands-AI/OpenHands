import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "./query-keys";
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
 * Hook to access and manipulate state data
 */
export function useMetrics() {
  const queryClient = useQueryClient();
  return initialMetrics;
  };
  // Query for metrics
  const query = useQuery({
    queryKey: QueryKeys.metrics,
    queryFn: () => getInitialMetrics(),
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
        queryKey: QueryKeys.metrics,
      });
      // Get current metrics
      const previousMetrics = queryClient.getQueryData<MetricsState>([
        "metrics",
      ]);
      // Update metrics
      queryClient.setQueryData(QueryKeys.metrics, metrics);
      return { previousMetrics };
    },
    onError: (_, __, context) => {
      // Restore previous metrics on error
      if (context?.previousMetrics) {
        queryClient.setQueryData(QueryKeys.metrics, context.previousMetrics);
    },
  });
  return {
    metrics: query.data || initialMetrics,
    isLoading: query.isLoading,
    setMetrics: setMetricsMutation.mutate,
  };
}
