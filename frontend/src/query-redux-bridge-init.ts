import { QueryClient } from "@tanstack/react-query";
import {
  initQueryReduxBridge,
  getQueryReduxBridge,
  SliceNames,
} from "./utils/query-redux-bridge";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the client wrapper
export function initializeBridge() {
  // Initialize the client wrapper with the query client
  initQueryReduxBridge(queryClient);
}

// Export a function to check if a slice is migrated (always returns true now)
export function isSliceMigrated(sliceName: SliceNames) {
  return true;
}
