import { QueryClient } from "@tanstack/react-query";
import { queryClientConfig } from "./query-client-config";

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);
