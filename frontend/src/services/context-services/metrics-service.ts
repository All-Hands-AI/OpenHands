import { Metrics } from "#/hooks/state/use-metrics";

// Global reference to the metrics update function
// This will be set by the MetricsProvider when it mounts
let updateMetricsFn: ((metrics: Metrics) => void) | null = null;

/**
 * Register the metrics update function
 * This should be called by the MetricsProvider when it mounts
 */
export function registerMetricsService(updateFn: (metrics: Metrics) => void) {
  updateMetricsFn = updateFn;
}

/**
 * Update metrics
 * This is used by the actions service
 */
export function updateMetrics(metrics: Metrics) {
  if (updateMetricsFn) {
    updateMetricsFn(metrics);
  }
}
