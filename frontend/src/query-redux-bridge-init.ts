import { QueryClient } from "@tanstack/react-query";
import { initQueryReduxBridge, SliceNames } from "./utils/query-redux-bridge";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the client wrapper
export function initializeBridge() {
  // Initialize the client wrapper with the query client
  initQueryReduxBridge(queryClient);
}

// Export a function to check if a slice is migrated (always returns true now)
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function isSliceMigrated(_sliceName?: SliceNames) {
  return true;
}
