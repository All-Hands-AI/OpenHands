import {
  QueryClientConfig,
  QueryCache,
  MutationCache,
} from "@tanstack/react-query";
import { retrieveAxiosErrorMessage } from "./utils/retrieve-axios-error-message";
import { displayErrorToast } from "./utils/custom-toast-handlers";

const shownErrors = new Set<string>();
export const queryClientConfig: QueryClientConfig = {
  defaultOptions: {
    queries: {
      // Keep data in cache for 1 hour
      staleTime: 60 * 60 * 1000,
      // Don't refetch on window focus
      refetchOnWindowFocus: false,
      // Don't garbage collect inactive queries
      gcTime: Infinity,
    },
  },
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (!query.meta?.disableToast) {
        const errorMessage = retrieveAxiosErrorMessage(error);

        if (!shownErrors.has(errorMessage)) {
          displayErrorToast(errorMessage || "An error occurred");
          shownErrors.add(errorMessage);

          setTimeout(() => {
            shownErrors.delete(errorMessage);
          }, 3000);
        }
      }
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _, __, mutation) => {
      if (!mutation?.meta?.disableToast) {
        const message = retrieveAxiosErrorMessage(error);
        displayErrorToast(message);
      }
    },
  }),
};
