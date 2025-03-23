import { metricsKeys } from "#/hooks/query/use-metrics";

interface MetricsState {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

// Get the query client
const getQueryClient = () =>
  // This is a workaround since we can't use hooks outside of components
  // In a real implementation, you might want to restructure this to use React context
  window.__queryClient;

// Helper function to get metrics functions
const getMetricsFunctions = () => {
  const queryClient = getQueryClient();
  if (!queryClient) {
    console.error("Query client not available");
    return null;
  }

  const setMetrics = (newMetrics: MetricsState) => {
    queryClient.setQueryData(metricsKeys.current(), newMetrics);
  };

  return {
    setMetrics,
  };
};

export function updateMetrics(metrics: MetricsState) {
  const metricsFunctions = getMetricsFunctions();
  if (metricsFunctions) {
    metricsFunctions.setMetrics(metrics);
  }
}
