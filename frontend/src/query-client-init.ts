import { QueryClient } from "@tanstack/react-query";
import { initQueryClientWrapper } from "./utils/query-client-wrapper";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the client wrapper
export function initializeQueryClient() {
  // Initialize the client wrapper with the query client
  initQueryClientWrapper(queryClient);
}
