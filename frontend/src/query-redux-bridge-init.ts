import { QueryClient } from "@tanstack/react-query";
import {
  initQueryReduxBridge,
  getQueryReduxBridge,
  SliceNames,
} from "./utils/query-redux-bridge";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the bridge
export function initializeBridge() {
  // Initialize the bridge with the query client
  initQueryReduxBridge(queryClient);

  // Mark the status slice as migrated to React Query
  getQueryReduxBridge().migrateSlice("status");
}

// Export a function to check if a slice is migrated
export function isSliceMigrated(sliceName: SliceNames) {
  try {
    return getQueryReduxBridge().isSliceMigrated(sliceName);
  } catch (error) {
    // If the bridge is not initialized, return false
    return false;
  }
}
