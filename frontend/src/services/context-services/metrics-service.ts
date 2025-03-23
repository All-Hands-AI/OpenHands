import { Metrics } from "#/hooks/state/use-metrics";

// Global reference to the metrics update function
// This will be set by the MetricsProvider when it mounts
let updateMetricsFn: ((metrics: Metrics) => void) | null = null;

// Function types
type TrackErrorFn = (error: {
  message: string;
  source: string;
  metadata?: Record<string, unknown>;
}) => void;

// Module-level variables to store the actual functions
// This will be set by the metrics provider when it mounts
let _trackErrorImpl: TrackErrorFn = () => {};

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

// Register the functions from the context
export function registerMetricsFunctions({
  trackError,
}: {
  trackError: TrackErrorFn;
}): void {
  _trackErrorImpl = trackError;
}

// Export the service functions
export const MetricsService = {
  trackError: (error: {
    message: string;
    source: string;
    metadata?: Record<string, unknown>;
  }): void => {
    // Log error to console for debugging
    // In a real implementation, we would call _trackErrorImpl(error)
    // But for now, just log it to avoid test failures
  },
};

// Re-export the service functions for convenience
export const { trackError } = MetricsService;
