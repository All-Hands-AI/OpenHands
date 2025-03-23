import React, { createContext, useContext, ReactNode, useEffect } from "react";
import { useMetrics, Metrics } from "#/hooks/state/use-metrics";
import { registerMetricsService } from "#/services/context-services/metrics-service";

interface MetricsContextType {
  metrics: Metrics;
  updateMetrics: (metrics: Metrics) => void;
  resetMetrics: () => void;
}

const MetricsContext = createContext<MetricsContextType | undefined>(undefined);

/**
 * Provider component for metrics
 */
export function MetricsProvider({ children }: { children: ReactNode }) {
  const metricsState = useMetrics();

  // Register the update function with the service
  useEffect(() => {
    registerMetricsService(metricsState.updateMetrics);
  }, [metricsState.updateMetrics]);

  return (
    <MetricsContext.Provider value={metricsState}>
      {children}
    </MetricsContext.Provider>
  );
}

/**
 * Hook to use the metrics context
 */
export function useMetricsContext() {
  const context = useContext(MetricsContext);

  if (context === undefined) {
    throw new Error("useMetricsContext must be used within a MetricsProvider");
  }

  return context;
}
