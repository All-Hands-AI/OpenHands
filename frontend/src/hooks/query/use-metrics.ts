import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface MetricsState {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

const initialState: MetricsState = {
  cost: null,
  usage: null,
};

// Define query keys
export const metricsKeys = {
  all: ["metrics"] as const,
  current: () => [...metricsKeys.all, "current"] as const,
};

// Custom hook to get and update metrics
export function useMetrics() {
  const queryClient = useQueryClient();

  // Query to get the current metrics
  const query = useQuery({
    queryKey: metricsKeys.current(),
    queryFn: () =>
      // Return the cached value or initial value
      queryClient.getQueryData<MetricsState>(metricsKeys.current()) ||
      initialState,
    // Initialize with the default metrics
    initialData: initialState,
  });

  // Mutation to update the metrics
  const mutation = useMutation({
    mutationFn: (newMetrics: MetricsState) => Promise.resolve(newMetrics),
    onSuccess: (newMetrics) => {
      queryClient.setQueryData(metricsKeys.current(), newMetrics);
    },
  });

  return {
    metrics: query.data,
    setMetrics: mutation.mutate,
    isLoading: query.isLoading,
  };
}
