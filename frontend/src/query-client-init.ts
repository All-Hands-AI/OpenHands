import { QueryClient } from "@tanstack/react-query";
import { initQueryClientWrapper, SliceNames } from "./utils/query-client-wrapper";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the client wrapper
export function initializeQueryClient() {
  // Initialize the client wrapper with the query client
  initQueryClientWrapper(queryClient);
}

// Export a function to check if a slice is migrated (always returns true now)
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function isSliceMigrated(_sliceName?: SliceNames) {
  return true;
}
