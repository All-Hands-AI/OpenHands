import {
  QueryClientConfig,
  QueryCache,
  MutationCache,
} from "@tanstack/react-query";
import { retrieveAxiosErrorMessage } from "./utils/retrieve-axios-error-message";
import { displayErrorToast } from "./utils/custom-toast-handlers";

const shownErrors = new Set<string>();

/**
 * React Query client configuration
 * This configuration sets up global error handling for queries and mutations
 */
export const queryClientConfig: QueryClientConfig = {
  // Default options for all queries
  defaultOptions: {
    queries: {
      // Retry failed queries 1 time after the initial failure
      retry: 1,
      // Keep cached data for 5 minutes
      gcTime: 1000 * 60 * 5,
      // Consider data fresh for 30 seconds
      staleTime: 1000 * 30,
      // Refetch on window focus after data becomes stale
      refetchOnWindowFocus: true,
      // Don't refetch on reconnect (handled by websockets)
      refetchOnReconnect: false,
    },
    mutations: {
      // Don't retry failed mutations by default
      retry: 0,
    },
  },

  // Global error handling for queries
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Skip toast if disableToast is set in query meta
      if (!query.meta?.disableToast) {
        const errorMessage = retrieveAxiosErrorMessage(error);

        // Prevent duplicate error toasts
        if (!shownErrors.has(errorMessage)) {
          displayErrorToast(errorMessage || "An error occurred");
          shownErrors.add(errorMessage);

          // Remove from shown errors after 3 seconds
          setTimeout(() => {
            shownErrors.delete(errorMessage);
          }, 3000);
        }
      }
    },
  }),

  // Global error handling for mutations
  mutationCache: new MutationCache({
    onError: (error, _, __, mutation) => {
      // Skip toast if disableToast is set in mutation meta
      if (!mutation?.meta?.disableToast) {
        const message = retrieveAxiosErrorMessage(error);
        displayErrorToast(message);
      }
    },
  }),
};
