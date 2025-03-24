import { useState, useEffect } from "react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

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
 * Hook to access and manipulate metrics data
 * This replaces the Redux metrics slice functionality without using React Query
 */
export function useMetrics() {
  const [metrics, setMetricsState] = useState<MetricsState>(initialMetrics);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from Redux on mount
  useEffect(() => {
    try {
      const bridge = getQueryReduxBridge();
      const reduxState = bridge.getReduxSliceState<MetricsState>("metrics");
      setMetricsState(reduxState);
    } catch (error) {
      // If we can't get the state from Redux, use the initial state
      // eslint-disable-next-line no-console
      console.warn("Could not get metrics from Redux, using default");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Function to update metrics
  const setMetrics = (newMetrics: MetricsState) => {
    setMetricsState(newMetrics);
  };

  // Ensure metrics always has valid values to prevent null reference errors
  const safeMetrics = {
    cost: metrics?.cost ?? null,
    usage: metrics?.usage ?? null,
  };

  return {
    metrics: safeMetrics,
    isLoading,
    setMetrics,
  };
}
