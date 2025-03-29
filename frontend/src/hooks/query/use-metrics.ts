import { useQuery, useQueryClient } from "@tanstack/react-query";

interface MetricsState {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

const initialMetrics: MetricsState = {
  cost: null,
  usage: null,
};

export const METRICS_QUERY_KEY = ["metrics"];

export function setMetrics(
  queryClient: ReturnType<typeof useQueryClient>,
  metrics: MetricsState,
) {
  queryClient.setQueryData(METRICS_QUERY_KEY, metrics);
}

export function useMetrics() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: METRICS_QUERY_KEY,
    queryFn: () => {
      const existingData =
        queryClient.getQueryData<MetricsState>(METRICS_QUERY_KEY);
      if (existingData) return existingData;
      return initialMetrics;
    },
    initialData: initialMetrics,
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const setMetricsState = (newMetrics: MetricsState) => {
    setMetrics(queryClient, newMetrics);
  };

  return {
    metrics: query.data || initialMetrics,
    isLoading: query.isLoading,
    setMetrics: setMetricsState,
  };
}
