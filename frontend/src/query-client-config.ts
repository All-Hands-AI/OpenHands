import {
  QueryClientConfig,
  QueryCache,
  MutationCache,
  QueryClient,
} from "@tanstack/react-query";
import { retrieveAxiosErrorMessage } from "./utils/retrieve-axios-error-message";
import { displayErrorToast } from "./utils/custom-toast-handlers";

const shownErrors = new Set<string>();
export const queryClientConfig: QueryClientConfig = {
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

// Create a global query client instance that can be used for manual invalidation
export const queryClient = new QueryClient(queryClientConfig);
