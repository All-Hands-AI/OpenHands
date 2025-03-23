import { queryClient } from "#/entry.client";
import { metricsKeys } from "#/hooks/query/use-metrics";

interface MetricsState {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

export function updateMetrics(metrics: MetricsState) {
  queryClient.setQueryData(metricsKeys.current(), metrics);
}
