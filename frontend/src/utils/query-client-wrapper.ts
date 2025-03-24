import { QueryClient } from "@tanstack/react-query";

// State slice names for query keys
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
   * Get the state for a slice from React Query
   */
  getSliceState<T>(sliceName: SliceNames): T {
    const queryKey = [sliceName];
    return (this.queryClient.getQueryData<T>(queryKey) || {}) as T;
  }

  /**
   * Set data for a query
   */
  setQueryData<T>(queryKey: unknown[], data: T): void {
    this.queryClient.setQueryData(queryKey, data);
  }
}

// Export a singleton instance
let queryClientWrapper: QueryClientWrapper | null = null;

export function initQueryClientWrapper(
  queryClient: QueryClient,
): QueryClientWrapper {
  queryClientWrapper = new QueryClientWrapper(queryClient);
  return queryClientWrapper;
}

export function getQueryClientWrapper(): QueryClientWrapper {
  if (!queryClientWrapper) {
    throw new Error(
      "QueryClientWrapper not initialized. Call initQueryClientWrapper first.",
    );
  }
  return queryClientWrapper;
}
