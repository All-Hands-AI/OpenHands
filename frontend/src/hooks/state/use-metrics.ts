import { useQueryClient } from "@tanstack/react-query";
import React from "react";

interface MetricsData {
  cost: number;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

const DEFAULT_METRICS: MetricsData = {
  cost: 0,
  usage: {
    prompt_tokens: 0,
    completion_tokens: 0,
    total_tokens: 0,
  },
};

const METRICS_KEY = ["_STATE", "metrics"];

export const useMetrics = () => {
  const queryClient = useQueryClient();

  const setMetrics = React.useCallback(
    (status: MetricsData) => {
      queryClient.setQueryData<MetricsData>(METRICS_KEY, status);
    },
    [queryClient],
  );

  const metrics =
    queryClient.getQueryData<MetricsData>(METRICS_KEY) ?? DEFAULT_METRICS;

  return { metrics, setMetrics };
};
