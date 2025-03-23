import { useState, useCallback } from "react";

export interface Metrics {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

const initialMetrics: Metrics = {
  cost: null,
  usage: null,
};

/**
 * Custom hook for managing metrics
 * This replaces the Redux metrics-slice
 */
export function useMetrics() {
  const [metrics, setMetricsState] = useState<Metrics>(initialMetrics);

  /**
   * Update metrics
   */
  const updateMetrics = useCallback((newMetrics: Metrics) => {
    setMetricsState(newMetrics);
  }, []);

  /**
   * Reset metrics to initial state
   */
  const resetMetrics = useCallback(() => {
    setMetricsState(initialMetrics);
  }, []);

  return {
    metrics,
    updateMetrics,
    resetMetrics,
  };
}
