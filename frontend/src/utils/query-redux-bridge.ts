import { QueryClient } from "@tanstack/react-query";

// Legacy type definitions kept for backward compatibility
export type SliceNames =
  | "chat"
  | "agent"
  | "browser"
  | "code"
  | "command"
  | "fileState"
  | "initialQuery"
  | "jupyter"
  | "securityAnalyzer"
  | "status"
  | "metrics";

/**
 * QueryClient wrapper that provides a simplified API for managing state
 * This replaces the previous Redux-Query bridge with a pure React Query implementation
 */
export class QueryClientWrapper {
  private queryClient: QueryClient;

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
  }

  /**
   * Update React Query data for a query
   */
  updateQueryData<T>(queryKey: unknown[], data: T): void {
    this.queryClient.setQueryData(queryKey, data);
  }

  /**
   * Get React Query data for a query
   */
  getQueryData<T>(queryKey: unknown[]): T | undefined {
    return this.queryClient.getQueryData<T>(queryKey);
  }

  /**
   * Invalidate a query to trigger a refetch
   */
  invalidateQuery(queryKey: unknown[]): void {
    this.queryClient.invalidateQueries({ queryKey });
  }

  /**
   * Reset a query to its initial state
   */
  resetQuery(queryKey: unknown[]): void {
    this.queryClient.resetQueries({ queryKey });
  }

  /**
   * Legacy method for backward compatibility
   * Get the state for a slice from React Query
   */
  getReduxSliceState<T>(sliceName: SliceNames): T {
    const queryKey = [sliceName];
    return (this.queryClient.getQueryData<T>(queryKey) || {}) as T;
  }

  /**
   * Legacy method for backward compatibility
   * Check if a slice has been migrated to React Query
   * @param _sliceName - The name of the slice to check (unused)
   */
  // eslint-disable-next-line class-methods-use-this, @typescript-eslint/no-unused-vars
  isSliceMigrated(_sliceName?: SliceNames): boolean {
    return true;
  }

  /**
   * Legacy method for backward compatibility
   * Sync data from Redux to React Query
   */
  syncReduxToQuery<T>(queryKey: unknown[], data: T): void {
    this.queryClient.setQueryData(queryKey, data);
  }

  /**
   * Legacy method for backward compatibility
   * Dispatch a Redux action
   * @param _sliceName - The name of the slice to dispatch to (unused)
   * @param _action - The action to dispatch (unused)
   */
  // eslint-disable-next-line class-methods-use-this, @typescript-eslint/no-unused-vars
  conditionalDispatch(
    _sliceName: SliceNames,
    _action: { type: string; payload?: unknown },
  ): void {
    // No-op - Redux is no longer used
  }
}

// Export a singleton instance
let queryClientWrapper: QueryClientWrapper | null = null;

export function initQueryReduxBridge(
  queryClient: QueryClient,
): QueryClientWrapper {
  queryClientWrapper = new QueryClientWrapper(queryClient);
  return queryClientWrapper;
}

export function getQueryReduxBridge(): QueryClientWrapper {
  if (!queryClientWrapper) {
    throw new Error(
      "QueryClientWrapper not initialized. Call initQueryReduxBridge first.",
    );
  }
  return queryClientWrapper;
}
