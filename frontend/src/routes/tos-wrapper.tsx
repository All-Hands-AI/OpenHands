import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import TOSPage from "./tos";

/**
 * This component wraps the TOS page with a separate QueryClient
 * to prevent any API calls from being made while on the TOS page.
 */
export default function TOSWrapper() {
  // Create a new QueryClient with defaultOptions that disable all queries
  const queryClient = React.useMemo(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Disable all queries by default
            enabled: false,
            // Don't retry failed queries
            retry: false,
            // Don't refetch on window focus
            refetchOnWindowFocus: false,
            // Don't refetch on reconnect
            refetchOnReconnect: false,
            // Don't refetch on mount
            refetchOnMount: false,
          },
        },
      }),
    [],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TOSPage />
    </QueryClientProvider>
  );
}
