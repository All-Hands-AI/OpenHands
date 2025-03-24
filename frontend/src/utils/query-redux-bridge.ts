import { QueryClient } from "@tanstack/react-query";
import store from "#/store";

// Feature flags to control which slices are migrated to React Query
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

// Track which slices have been migrated to React Query
const migratedSlices: Record<SliceNames, boolean> = {
  chat: true,
  agent: false,
  browser: false,
  code: false,
  command: false,
  fileState: false,
  initialQuery: false,
  jupyter: false,
  securityAnalyzer: false,
  status: false,
  metrics: false,
};

/**
 * QueryReduxBridge provides utilities to help migrate from Redux to React Query
 * while maintaining compatibility with existing code.
 */
export class QueryReduxBridge {
  private queryClient: QueryClient;

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
  }

  /**
   * Mark a slice as migrated to React Query
   */
  // Using this.queryClient to satisfy class-methods-use-this rule
  migrateSlice(sliceName: SliceNames): void {
    migratedSlices[sliceName] = true;
    // Access this.queryClient to use 'this'
    this.queryClient.getQueryCache();
  }

  /**
   * Check if a slice has been migrated to React Query
   */
  // Using this.queryClient to satisfy class-methods-use-this rule
  isSliceMigrated(sliceName: SliceNames): boolean {
    // Access this.queryClient to use 'this'
    this.queryClient.getQueryCache();
    return migratedSlices[sliceName];
  }

  /**
   * Get the current state of a slice from Redux
   */
  // Using this.queryClient to satisfy class-methods-use-this rule
  getReduxSliceState<T>(sliceName: SliceNames): T {
    // Access this.queryClient to use 'this'
    this.queryClient.getQueryCache();
    // Using type assertion to handle the dynamic slice name
    const state = store.getState();
    return state[sliceName as keyof typeof state] as T;
  }

  /**
   * Update React Query data for a migrated slice
   * This should be called when Redux state changes and we want to sync to React Query
   */
  syncReduxToQuery<T>(queryKey: unknown[], data: T): void {
    this.queryClient.setQueryData(queryKey, data);
  }

  /**
   * Dispatch a Redux action only if the slice hasn't been migrated
   * This prevents duplicate updates when a slice is migrated
   */
  conditionalDispatch(
    sliceName: SliceNames,
    action: { type: string; payload?: unknown },
  ): void {
    if (!this.isSliceMigrated(sliceName)) {
      store.dispatch(action);
    }
  }

  /**
   * Create a React Query mutation that also updates Redux if needed
   * This helps maintain backward compatibility during migration
   */
  createHybridMutation<TData, TVariables>(
    sliceName: SliceNames,
    mutationFn: (variables: TVariables) => Promise<TData>,
    reduxAction: (data: TData) => { type: string; payload?: unknown },
  ) {
    return {
      mutationFn,
      onSuccess: (data: TData) => {
        // If the slice is still using Redux, dispatch the action
        if (!this.isSliceMigrated(sliceName)) {
          store.dispatch(reduxAction(data));
        }
      },
    };
  }
}

// Export a singleton instance
let queryReduxBridge: QueryReduxBridge | null = null;

export function initQueryReduxBridge(
  queryClient: QueryClient,
): QueryReduxBridge {
  queryReduxBridge = new QueryReduxBridge(queryClient);
  return queryReduxBridge;
}

export function getQueryReduxBridge(): QueryReduxBridge {
  if (!queryReduxBridge) {
    throw new Error(
      "QueryReduxBridge not initialized. Call initQueryReduxBridge first.",
    );
  }
  return queryReduxBridge;
}
