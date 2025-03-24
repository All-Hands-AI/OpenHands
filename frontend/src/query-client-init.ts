import { QueryClient } from "@tanstack/react-query";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the query client
export function initializeQueryClient() {
  // Nothing to do here, just return the query client
  return queryClient;
}
